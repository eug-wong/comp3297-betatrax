# BetaTrax Sprint 1 Demo Guide

## Before Demo

```bash
# 1. Reset database and set up demo data
rm -f db.sqlite3
python manage.py migrate
python manage.py shell < demo_setup.py

# 2. Start server
python manage.py runserver
```

## Login Credentials
- **Product Owner:** `productowner` / `pass123`
- **Developer:** `dev1` / `pass123`

---

## Demo Flow (Browser)

### Step 1: Submit defect report
**URL:** http://localhost:8000/api/defects/

POST this JSON:
```json
{
    "title": "Hit count incorrect",
    "description": "Following a successful search, the hit count is different to the number of matches displayed.",
    "steps_to_reproduce": "1. Enter search criteria\n2. Search\n3. Compare matches with hit count",
    "product": 1,
    "tester_id": "Tester_1",
    "tester_email": "icyreward@gmail.com"
}
```

---

### Step 2: PO - List New defects
**Login as:** `productowner`
**URL:** http://localhost:8000/api/po/defects/new/

---

### Step 3: PO - View target defect details
**URL:** http://localhost:8000/api/po/defects/3/

---

### Step 4: PO - Accept defect
**URL:** http://localhost:8000/api/po/defects/3/approve/

POST this JSON:
```json
{
    "severity": "Minor",
    "priority": "High",
    "backlog_item_id": "PBI-003"
}
```

---

### Step 5: Developer - List Open defects
**Login as:** `dev1`
**URL:** http://localhost:8000/api/developer/defects/open/

---

### Step 6: Developer - View target defect
**URL:** http://localhost:8000/api/developer/defects/3/

---

### Step 7: Developer - Take responsibility
**URL:** http://localhost:8000/api/developer/defects/3/take-responsibility/

Click POST

---

### Step 8: Developer - List Open defects (should be empty)
**URL:** http://localhost:8000/api/developer/defects/open/

---

### Step 9: Developer - Mark as Fixed
**URL:** http://localhost:8000/api/developer/defects/3/mark-as-fixed/

Click POST

---

### Step 10: Verify Fixed status
**URL:** http://localhost:8000/api/developer/defects/3/

---

### Step 11: PO - Close as Resolved
**Login as:** `productowner`
**URL:** http://localhost:8000/api/defects/3/resolve/

PATCH this JSON:
```json
{
    "status": "Resolved"
}
```

---

## Expected Flow
```
New → Open → Assigned → Fixed → Resolved
```
