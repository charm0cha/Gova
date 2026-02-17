from dotenv import load_dotenv
import httpx
import logging
from fastapi import FastAPI, Request, Depends, status, Form, Cookie, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import SessionLocal, UserTable, engine, Base
import os


load_dotenv()
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


app = FastAPI()
templates = Jinja2Templates(directory="templates")
logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def send_expiry_email(manager_name: str, contractor_name: str, expiry_date: datetime):
    # 1. Setup the Email Content
    subject = f"ACTION REQUIRED: Contractor Access Expiry - {contractor_name}"
    body = f"""
    <h2>GOVA Control Plane Alert</h2>
    <p>Hi <strong>{manager_name}</strong>,</p>
    <p>This is an automated notification regarding <strong>{contractor_name}</strong>.</p>
    <p>Their contract and system access is scheduled to expire on <strong>{expiry_date.strftime('%Y-%m-%d')}</strong> (in 14 days).</p>
    <p>Please log in to the Gova portal to extend or revoke this access.</p>
    <br>
    <p><em>Security Note: Failure to act will result in automatic offboarding.</em></p>
    """



@app.get("/auth/notify-managers")
async def trigger_notifications(db: Session = Depends(get_db)):
    # 1. Define the "2 weeks from now" target
    today = datetime.now().date()
    target_date = today + timedelta(days=7)
    
    # 2. Query users expiring on that specific day
    expiring_soon = db.query(UserTable).all()
    
    notified_count = 0
    for user in expiring_soon:
        if user.contract_end and user.contract_end.date() == target_date:
            send_expiry_email(user.manager_name, user.full_name, user.contract_end)
            notified_count += 1
            
    return {"status": "Process Complete", "emails_sent": notified_count} 
   

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def handle_login(username: str = Form(...), password: str = Form(...)):
    if username == "admin@gova.com" and password == "123":
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="is_logged_in", value="true", httponly=True)
        return response
    return RedirectResponse(url="/login?error=invalid", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/")
async def read_inventory(request: Request, is_logged_in: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if not is_logged_in:
        return RedirectResponse(url="/login")
    
    users = db.query(UserTable).all()
    for user in users:
        user.display_location = getattr(user, 'location', 'Remote') or 'Remote'
        user.display_manager = getattr(user, 'manager_name', 'Not Assigned') or 'Not Assigned'
        
        if user.contract_end:
            user.days_left = (user.contract_end - datetime.now()).days
            user.is_expiring = user.days_left < 30
        else:
            user.days_left = 365
            user.is_expiring = False
            
    stats = db.query(UserTable.dept, func.count(UserTable.dept)).group_by(UserTable.dept).all()
    return templates.TemplateResponse("inventory.html", {
        "request": request, 
        "users": users, 
        "dept_counts": {d: c for d, c in stats if d}
    })
@app.get("/auth/sync")
async def sync_with_microsoft(db: Session = Depends(get_db)):
    try:
        # Token Logic (using your working Secret Value)
        token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
        async with httpx.AsyncClient() as client:
            token_res = await client.post(token_url, data={
                "client_id": {CLIENT_ID}, "client_secret": {CLIENT_SECRET},
                "scope": "https://graph.microsoft.com/.default", "grant_type": "client_credentials"
            })
            token = token_res.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # Graph Call
            users_url = (
                "https://graph.microsoft.com/v1.0/users"
                "?$top=999"
                "&$select=displayName,userPrincipalName,department,jobTitle,officeLocation"
                "&$expand=manager($select=displayName)"
            )
            users_res = await client.get(users_url, headers=headers)
            ms_users = users_res.json().get("value", [])

        added = 0
        for ms_user in ms_users:
            display_name = ms_user.get("displayName") or ""
            if "(FL)" in display_name.upper():
                email = ms_user.get("userPrincipalName")
                exists = db.query(UserTable).filter(UserTable.email == email).first()
                
                if not exists:
                    manager_obj = ms_user.get("manager")
                    mgr_name = manager_obj.get("displayName") if manager_obj else "HR Admin"

                    new_user = UserTable(
                        full_name=display_name,
                        email=email,
                        dept=ms_user.get("department") or "General", # Stores Dept
                        role=ms_user.get("jobTitle") or "Freelancer", # Stores Role
                        location=ms_user.get("officeLocation") or "Remote",
                        manager_name=mgr_name,
                        created_at=datetime.now(),
                        contract_end=datetime.now() + timedelta(days=90) # Default 90 day lifecycle
                    )
                    db.add(new_user)
                    added += 1
        
        db.commit()
        return RedirectResponse(url=f"/?msg=sync_success&added={added}")
    except Exception as e:
        logging.error(f"SYNC ERROR: {e}")
        return RedirectResponse(url="/?msg=sync_error")
        


# --- NOTIFICATION LOGIC ---
@app.get("/notify-managers")
async def notify_managers(db: Session = Depends(get_db)):
    """
    Finds contractors with (FL) whose contract ends in 7 days.
    """
    threshold = datetime.now() + timedelta(days=7)
    expiring = db.query(UserTable).filter(UserTable.contract_end <= threshold).all()
    
    for user in expiring:
        # Placeholder for your next step: SMTP or Teams Alert
        logging.info(f"ALERT: Sending notification to {user.manager_name} for {user.full_name}")
        
    return {"status": "success", "notified_count": len(expiring)}

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("is_logged_in")
    return response

@app.post("/delete/{user_id}")
async def delete_user(user_id: int, is_logged_in: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if not is_logged_in: return RedirectResponse(url="/login")
    user = db.query(UserTable).filter(UserTable.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)