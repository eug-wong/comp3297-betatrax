# BetaTrax

Defect tracking system for beta testing.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install django djangorestframework
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Working Features

- [x] Submit defect report with optional email
- [x] PO view and list New defects
- [x] PO accept defect with Severity/Priority
- [x] Developer view and list Open defects
- [x] Developer take responsibility for defect
- [x] Developer mark defect as Fixed
- [x] Developer mark defect as Cannot Reproduce
- [x] PO close defect as Resolved
- [x] Email notifications (console backend)

## Not Implemented

- [ ] PO reject defect
- [ ] PO mark defect as Duplicate
- [ ] Reopen defect flow
- [ ] Comments on defects
