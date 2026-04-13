"""URL configuration for defects app."""
from django.urls import path

from . import views

urlpatterns = [
    path('api/defects/', views.defect_list, name='defect_list'),
    path('api/defects/<int:defect_id>/', views.defect_detail, name='defect_detail'),

    # Current developer routes
    path('api/defects/<int:defect_id>/assign/', views.take_responsibility, name='take_responsibility'),
    path('api/defects/<int:defect_id>/mark-fixed/', views.mark_as_fixed, name='mark_as_fixed'),
    path('api/defects/<int:defect_id>/mark-cannot-reproduce/', views.mark_as_cannot_reproduce, name='mark_as_cannot_reproduce'),

    # Compatibility developer routes
    path('api/developer/defects/open/', views.list_open_defects, name='list_open_defects'),
    path('api/developer/defects/list/', views.list_defects, name='developer_list_defects'),
    path('api/developer/defects/<int:defect_id>/', views.view_defect_detail, name='view_defect_detail'),
    path('api/developer/defects/<int:defect_id>/take-responsibility/', views.take_responsibility, name='take_responsibility_legacy'),
    path('api/developer/defects/<int:defect_id>/mark-as-fixed/', views.mark_as_fixed, name='mark_as_fixed_legacy'),
    path('api/developer/defects/<int:defect_id>/mark-as-cannot-reproduce/', views.mark_as_cannot_reproduce, name='mark_as_cannot_reproduce_legacy'),

    # Product owner routes
    path('api/defects/<int:defect_id>/approve/', views.approve_defect, name='approve_defect'),
    path('api/defects/<int:defect_id>/reject/', views.reject_defect, name='reject_defect'),
    path('api/defects/<int:defect_id>/mark-duplicate/', views.mark_duplicate, name='mark_duplicate'),
    path('api/defects/<int:defect_id>/reopen/', views.reopen_defect, name='reopen_defect'),
    path('api/defects/<int:defect_id>/resolve/', views.resolve_defect, name='resolve_defect'),

    # Compatibility PO routes
    path('api/po/defects/new/', views.po_new_defect_list, name='po_new_defect_list'),
    path('api/po/defects/list/', views.po_defect_list, name='po_defect_list'),
    path('api/po/defects/<int:defect_id>/', views.po_defect_detail, name='po_defect_detail'),
    path('api/po/defects/<int:defect_id>/approve/', views.approve_defect, name='po_approve_defect'),
    path('api/po/defects/<int:defect_id>/reject/', views.reject_defect, name='po_reject_defect'),
    path('api/po/defects/<int:defect_id>/mark-duplicate/', views.mark_duplicate, name='po_mark_duplicate'),
    path('api/po/defects/<int:defect_id>/reopen/', views.reopen_defect, name='po_reopen_defect'),
    path('api/po/defects/<int:pk>/resolve/', views.resolve_defect, name='po_resolve_defect'),
]
