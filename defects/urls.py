"""
URL configuration for defects app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('api/defects/', views.submit_defect, name='submit_defect'),
    # Developer endpoints
    path('api/developer/defects/open/', views.list_open_defects, name='list_open_defects'),
    path('api/developer/defects/<int:defect_id>/', views.view_defect_detail, name='view_defect_detail'),
    path('api/developer/defects/<int:defect_id>/take-responsibility/', views.take_responsibility, name='take_responsibility'),
    path('api/developer/defects/<int:defect_id>/mark-as-fixed/', views.mark_as_fixed, name='mark_as_fixed'),
    path('api/developer/defects/<int:defect_id>/mark-as-cannot-reproduce/', views.mark_as_cannot_reproduce, name='mark_as_cannot_reproduce'),
    path('api/defects/<int:pk>/resolve/', views.resolve_defect, name='resolve-defect'),
]
