from django.contrib import admin
from .models import Product, Developer, DefectReport, Comment

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    search_fields = ('name', 'owner__username')

@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ('user', 'product')
    list_filter = ('product',)
    search_fields = ('user__username', 'product__name')

@admin.register(DefectReport)
class DefectReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'product', 'status', 'severity', 'priority', 'assigned_developer', 'created_at')
    list_filter = ('status', 'severity', 'priority', 'product', 'created_at')
    search_fields = ('title', 'description', 'tester_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'steps_to_reproduce', 'product')
        }),
        ('Tester Info', {
            'fields': ('tester_id', 'tester_email')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'assigned_developer', 'severity', 'priority')
        }),
        ('Deduplication', {
            'fields': ('duplicate_of',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'defect_report', 'date')
    list_filter = ('date', 'author')
    search_fields = ('text', 'author__username', 'defect_report__title')
    readonly_fields = ('date',)
