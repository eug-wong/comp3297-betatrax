# BetaTrax
Defect tracking system for beta testing - Now upgraded with PostgreSQL and Multi-tenancy support.

# Project Overview
BetaTrax is a specialized platform for managing software defects across multiple organizations. By utilizing a schema-based multi-tenancy approach (via django-tenants), it ensures complete data isolation between different tenants (e.g., different universities) while running on a single server instance.

# Prerequisites
1. Python 3.14+

2. PostgreSQL: Ensure PostgreSQL is running and a database (e.g., betatrax_db) is created.

3. Hosts File Configuration: To enable local tenant routing, add the following to your system's hosts file (/etc/hosts on macOS/Linux):

127.0.0.1 localhost
127.0.0.1 hku.localhost
127.0.0.1 polyu.localhost

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
4. Create Tenants (e.g., HKU and PolyU)
In the same shell, set up your isolated tenant environments:

```python
# Create HKU tenant
hku = Client(schema_name='hku', name='HKU University')
hku.save()
Domain.objects.create(domain='hku.localhost', tenant=hku, is_primary=True)

# Create PolyU tenant
polyu = Client(schema_name='polyu', name='PolyU Tenant')
polyu.save()
Domain.objects.create(domain='polyu.localhost', tenant=polyu, is_primary=True)
```
5. Create Administrative Users

Global Admin: 
```bash
python manage.py createsuperuser 
```
(Access via: localhost:8000/admin/)

Tenant Admin: 
```bash
python manage.py tenant_command createsuperuser --schema=hku 
```
(Access via hku.localhost:8000/admin/)

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

## Not Implemented
- [ ] Defect report validation
- [ ] Version field on defect report
- [ ] PO Assign Defect to Developer
