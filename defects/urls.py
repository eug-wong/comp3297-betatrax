"""URL configuration for defects app."""
from django.urls import path
from . import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('api/defects/', views.defect_list, name='defect_list'),
    path('api/defects/<int:defect_id>/', views.defect_detail, name='defect_detail'),

    # developer actions
    path('api/defects/<int:defect_id>/assign/', views.take_responsibility, name='take_responsibility'),
    path('api/defects/<int:defect_id>/mark-fixed/', views.mark_as_fixed, name='mark_as_fixed'),
    path('api/defects/<int:defect_id>/mark-cannot-reproduce/', views.mark_as_cannot_reproduce, name='mark_as_cannot_reproduce'),

    # product owner actions
    path('api/defects/<int:defect_id>/approve/', views.approve_defect, name='approve_defect'),
    path('api/defects/<int:defect_id>/reject/', views.reject_defect, name='reject_defect'),
    path('api/defects/<int:defect_id>/mark-duplicate/', views.mark_duplicate, name='mark_duplicate'),
    path('api/defects/<int:defect_id>/reopen/', views.reopen_defect, name='reopen_defect'),
    path('api/defects/<int:defect_id>/resolve/', views.resolve_defect, name='resolve_defect'),

    path('api/defects/<int:defect_id>/comments/', views.defect_comments, name='defect_comments'),
    path('api/products/', views.create_product, name='create_product'),
    path('api/auth/logout/', views.logout_view, name='api_logout'),

    # developer effectiveness metric
    path('api/employees/<int:employee_id>/effectiveness/', views.developer_effectiveness, name='developer_effectiveness'),

    #schema endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
