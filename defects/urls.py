"""
URL configuration for defects app.
"""
from django.urls import path
from . import views
from . import po_views

urlpatterns = [
    # Defect collection — POST to submit (no auth), GET to list (dev or PO, ?status= filter)
    path('api/defects/', views.defect_list, name='defect_list'),
    # Defect detail — works for both dev and PO
    path('api/defects/<int:defect_id>/', views.defect_detail, name='defect_detail'),

    # Developer actions
    path('api/defects/<int:defect_id>/assign/', views.take_responsibility, name='take_responsibility'),
    path('api/defects/<int:defect_id>/mark-fixed/', views.mark_as_fixed, name='mark_as_fixed'),
    path('api/defects/<int:defect_id>/mark-cannot-reproduce/', views.mark_as_cannot_reproduce, name='mark_as_cannot_reproduce'),

    # Product Owner actions
    path('api/defects/<int:defect_id>/approve/', po_views.POApproveDefect.as_view(), name='po_approve_defect'),
    path('api/defects/<int:defect_id>/resolve/', po_views.POResolveDefect.as_view(), name='po_resolve_defect'),
]
