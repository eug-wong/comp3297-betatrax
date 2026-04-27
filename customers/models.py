from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Client(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    # schema_name 會由 TenantMixin 自動建立，用來對應 PostgreSQL 的 Schema

class Domain(DomainMixin):
    pass