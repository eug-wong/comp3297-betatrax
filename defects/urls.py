"""
URL configuration for defects app.
"""
from django.urls import path
from . import views
from . import po_views

urlpatterns = [
    path('api/defects/', views.submit_defect, name='submit_defect'),
    # Developer endpoints
    path('api/developer/defects/open/', views.list_open_defects, name='list_open_defects'),
    path('api/developer/defects/list/', views.list_defects, name='list_defects'),
    path('api/developer/defects/<int:defect_id>/', views.view_defect_detail, name='view_defect_detail'),
    path('api/developer/defects/<int:defect_id>/take-responsibility/', views.take_responsibility, name='take_responsibility'),
    path('api/developer/defects/<int:defect_id>/mark-as-fixed/', views.mark_as_fixed, name='mark_as_fixed'),
    path('api/developer/defects/<int:defect_id>/mark-as-cannot-reproduce/', views.mark_as_cannot_reproduce, name='mark_as_cannot_reproduce'),
    path('api/po/defects/<int:pk>/resolve/', views.resolve_defect, name='resolve-defect'),
    # API endpoints for Product Owner functions
    path('api/po/defects/new/', po_views.PO_NewDefectList.as_view()),
    path('api/po/defects/<int:defect_id>/', po_views.PO_DefectDetail.as_view()),
    path('api/po/defects/<int:defect_id>/approve/', po_views.PO_ApproveDefect.as_view()),
    path('api/po/defects/<int:defect_id>/reject/', po_views.PO_RejectDefect.as_view()),
    path('api/po/defects/<int:defect_id>/mark-duplicate/', po_views.PO_MarkDefectDuplicate.as_view()),
    path('api/po/defects/<int:defect_id>/reopen/', po_views.PO_ReopenDefect.as_view()),
    path('api/po/defects/list/', po_views.PO_DefectList.as_view()),

]
