# GOVA: Enterprise Contractor Governance & Lifecycle Platform

## Overview
**GOVA** (Governance & Oversight Visual Analytics) is a specialised control plane designed to solve the "External Workforce Problem." In large enterprises, tracking when contractors (FL) lose access is a major security risk. 

GOVA automates the **discovery, monitoring, and offboarding** of external users by integrating directly with **Microsoft Entra ID (Azure AD)**.



---

## Key Features

### Automated Identity Synchronization
* Connects to **Microsoft Graph API** using OAuth2 Client Credentials.
* Intelligently filters for external identities (tagged with `(FL)`).
* Maps complex enterprise hierarchies (Department, Job Titles, and Manager data).

### Lifecycle Guard
* **Predictive Tracking:** Automatically calculates "Days Left" for every contractor.
* **Manager Notifications:** Background logic identifies accounts expiring in 7 days and triggers automated email alerts to the direct manager.
* **Inventory Dashboard:** A unified view of the external workforce with real-time status indicators.

### Security & Compliance
* **Secure Authentication:** Implements HttpOnly cookies for session management.
* **Audit-Ready:** Tracks creation dates and contract end-dates in a structured SQL database.

---

## Tech Stack
* **Backend:** Python 3.x, FastAPI
* **Identity:** Microsoft Graph API (OIDC/OAuth2)
* **Database:** SQLAlchemy ORM (PostgreSQL/SQLite)
* **Frontend:** Jinja2 Templates & Tailwind-style UI logic
* **Communication:** SMTP for automated manager alerts

---

## Setup & Installation

1. **Environment Variables:**
   Create a `.env` file with your Azure App Registration details:
   ```env
   TENANT_ID=your-microsoft-tenant-id
   CLIENT_ID=your-client-id
   CLIENT_SECRET=your-client-secret

   ```
 2. Install Dependencies:

```Bash
pip install -r requirements.txt
```
3. Run the Platform:
```
Bash
uvicorn main:app --reload
```

## Author
Charmaine Olupitan
* Technical Engineer and Developer.
