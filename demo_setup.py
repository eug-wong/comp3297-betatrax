#!/usr/bin/env python
"""
Run this before the demo:
    rm -f db.sqlite3
    python manage.py migrate
    python manage.py shell < demo_setup.py
    python manage.py runserver
"""
from django.contrib.auth.models import User
from defects.models import Product, Developer, DefectReport

# Clear existing data
DefectReport.objects.all().delete()
Developer.objects.all().delete()
Product.objects.all().delete()
User.objects.filter(username__in=['productowner', 'dev1']).delete()

# Reset SQLite auto-increment counters so IDs start from 1
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='defects_defectreport'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='defects_product'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='defects_developer'")

# Create Product Owner
po = User.objects.create_user('productowner', 'po@test.com', 'pass123', is_staff=True)

# Create Developer
dev_user = User.objects.create_user('dev1', 'dev@test.com', 'pass123', is_staff=True)

# Create Product (Prod_1) - will be ID 1
product = Product.objects.create(name='Prod_1', owner=po)

# Create Developer linked to product
developer = Developer.objects.create(user=dev_user, product=product)

# Defect Report 1: "Unable to search" - Status: Assigned (ID 1)
defect1 = DefectReport.objects.create(
    title="Unable to search",
    description="Search button unresponsive after completing an initial search",
    steps_to_reproduce="1. Complete a search\n2. Modify search criteria\n3. Click Search button",
    product=product,
    tester_id="Tester_1",
    tester_email="icyreward@gmail.com",
    status="Assigned",
    severity="Major",
    priority="High",
    assigned_developer=developer
)

# Defect Report 2: "Poor readability in dark mode" - Status: New (ID 2)
defect2 = DefectReport.objects.create(
    title="Poor readability in dark mode",
    description="Text unclear in dark mode due to lack of contrast with background",
    steps_to_reproduce="1. Enable dark mode\n2. Display text",
    product=product,
    tester_id="Tester_2",
    tester_email=None,
    status="New"
)

print("=" * 50)
print("DEMO SETUP COMPLETE")
print("=" * 50)
print(f"Product: {product.name} (ID: {product.id})")
print(f"Product Owner: productowner / pass123")
print(f"Developer: dev1 / pass123")
print(f"Defect {defect1.id}: '{defect1.title}' - {defect1.status}")
print(f"Defect {defect2.id}: '{defect2.title}' - {defect2.status}")
print("=" * 50)
print()
print("Next: Submit new defect via API, it will be ID 3")
print("=" * 50)
