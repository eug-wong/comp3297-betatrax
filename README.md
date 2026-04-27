# BetaTrax (Release 2)
Defect tracking system for beta testing - Upgraded to a **Multi-tenant SaaS architecture**.

## Project Overview
BetaTrax supports the beta testing lifecycle for software products. This release introduces a single database, separate schema multi-tenancy approach using PostgreSQL, allowing different organizations to use the service as a SaaS product with total data isolation.

## Prerequisites
1. Python 3.14+ 
2. PostgreSQL: Required for schema-based multi-tenancy.
3. Hosts File Configuration: Map local subdomains to enable tenant routing:
```text
127.0.0.1 localhost
127.0.0.1 compa.localhost
127.0.0.1 compb.localhost
```

## Setup

1. Environment & Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install django djangorestframework django-tenants psycopg2-binary
```
2. Database Migration
Initialize the PostgreSQL schemas for both shared (public) and tenant-specific applications:

```bash
python manage.py migrate_schemas --shared
```
3. Initialize the Public Interface (Mandatory)
The public schema acts as the management layer for all tenants. Open the Django shell:

```bash
python manage.py shell
```
Run the following script:

```python
from customers.models import Client, Domain

# Create the public tenant
tenant = Client(schema_name='public', name='Public Interface')
tenant.save()
Domain.objects.create(domain='localhost', tenant=tenant, is_primary=True)
```
# 4. Create Tenants (Example for different development companies)
# In the same shell, set up your isolated tenant environments:

```python
# Create Company A tenant
company_a = Client(schema_name='comp_a', name='Software Solutions Ltd')
company_a.save()
Domain.objects.create(domain='compa.localhost', tenant=company_a, is_primary=True)

# Create Company B tenant
company_b = Client(schema_name='comp_b', name='InnovateSoft')
company_b.save()
Domain.objects.create(domain='compb.localhost', tenant=company_b, is_primary=True)
```

5. Create Administrative Users

Global Admin: 
```bash
python manage.py createsuperuser 
```
(Access via: localhost:8000/admin/)

Tenant Admin: 
```bash
python manage.py tenant_command createsuperuser --schema=comp_a
```
(Access via compa.localhost:8000/admin/)

6. Launch Server
```bash
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
- [x] PO reject defect
- [x] PO mark defect as Duplicate
- [x] Reopen defect flow
- [x] Comments on defects
- [x] Product Registration by Product Owner
- [x] User Authentication