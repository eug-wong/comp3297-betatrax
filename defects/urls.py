from django.urls import path
from .views import resolve_defect

urlpatterns = [
    path('<int:pk>/resolve/', resolve_defect, name='resolve-defect'),
]