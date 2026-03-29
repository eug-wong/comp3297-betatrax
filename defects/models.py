# models.py
# Django models for the defects app.

from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    """A software product registered with BetaTrax."""
    name = models.CharField(max_length=255)
    # One-to-one with Product Owner (a User)
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='owned_product'
    )

    def __str__(self):
        return self.name


class Developer(models.Model):
    """A developer assigned to a product. Many developers per product."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Many-to-one: many developers belong to one product
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='developers'
    )

    def __str__(self):
        return self.user.username


class DefectReport(models.Model):
    """A defect report submitted by a tester."""

    # Status choices (Sprint 1: New -> Open -> Assigned -> Fixed -> Resolved)
    STATUS_CHOICES = [
        ('New', 'New'),
        ('Open', 'Open'),
        ('Assigned', 'Assigned'),
        ('Fixed', 'Fixed'),
        ('Resolved', 'Resolved'),
        ('Rejected', 'Rejected'),
        ('Duplicate', 'Duplicate'),
        ('Cannot Reproduce', 'Cannot Reproduce'),
        ('Reopened', 'Reopened'),
    ]

    SEVERITY_CHOICES = [
        ('Critical', 'Critical'),
        ('Major', 'Major'),
        ('Minor', 'Minor'),
        ('Low', 'Low'),
    ]

    PRIORITY_CHOICES = [
        ('Critical', 'Critical'),
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]

    # Core fields
    title = models.CharField(max_length=255)
    description = models.TextField()
    steps_to_reproduce = models.TextField()

    # Relationships
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='defect_reports'
    )

    # Tester info (not a Django user - external beta tester)
    tester_id = models.CharField(max_length=100)
    tester_email = models.EmailField(blank=True, null=True)  # Optional

    # Workflow fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='New'
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        blank=True,
        null=True
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        blank=True,
        null=True
    )

    # Assigned developer (set when status -> Assigned)
    assigned_developer = models.ForeignKey(
        Developer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_defects'
    )

    # For duplicate tracking
    duplicate_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='duplicates'
    )

    # PO approval fields
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_defects'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    backlog_item_link = models.CharField(max_length=100, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)  # time_received
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}: {self.title}"


class Comment(models.Model):
    """Comments attached to a defect report by Developer or Product Owner."""
    defect_report = models.ForeignKey(
        DefectReport,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    # Author can be any User (Developer or Product Owner)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.defect_report.id}"
