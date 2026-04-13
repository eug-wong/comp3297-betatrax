"""
URL configuration for defects app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # list + submit
    path('api/defects/', views.defect_list, name='defect_list'),
    path('api/defects/<int:defect_id>/', views.defect_detail, name='defect_detail'),

    # developer
    path('api/defects/<int:defect_id>/assign/', views.take_responsibility, name='take_responsibility'),
    path('api/defects/<int:defect_id>/mark-fixed/', views.mark_as_fixed, name='mark_as_fixed'),
    path('api/defects/<int:defect_id>/mark-cannot-reproduce/', views.mark_as_cannot_reproduce, name='mark_as_cannot_reproduce'),

    # product owner
    path('api/defects/<int:defect_id>/approve/', views.approve_defect, name='approve_defect'),
    path('api/defects/<int:defect_id>/resolve/', views.resolve_defect, name='resolve_defect'),
]
