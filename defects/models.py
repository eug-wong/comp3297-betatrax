# models.py
from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    """A software product registered with BetaTrax."""
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Employee(models.Model):
    """A company employee who is either a Developer or Product Owner for a product."""
    ROLE_CHOICES = [
        ('Developer', 'Developer'),
        ('ProductOwner', 'Product Owner'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='employees'
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class DefectReport(models.Model):
    """A defect report submitted by a tester."""

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

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='defect_reports'
    )

    # Tester info (external beta tester, not a Django user)
    tester_id = models.CharField(max_length=100)
    tester_email = models.EmailField(blank=True, null=True)

    # Workflow fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, blank=True, null=True)

    # Set when a developer takes responsibility
    assigned_developer = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_defects'
    )

    # Duplicate tracking
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

    # PO rejection fields
    rejected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_defects'
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    # PO reopen fields
    reopened_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reopened_defects'
    )
    reopened_at = models.DateTimeField(null=True, blank=True)
    reopen_reason = models.TextField(blank=True, null=True)

    # Developer cannot reproduce fields
    cannot_reproduce_reason = models.TextField(blank=True, null=True)
    cannot_reproduced_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cannot_reproduced_defects'
    )
    cannot_reproduced_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}: {self.title}"


class Comment(models.Model):
    """Comments attached to a defect report by a Developer or Product Owner."""
    defect_report = models.ForeignKey(
        DefectReport,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.defect_report.id}"
