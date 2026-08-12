from django.urls import path
from .views import LoginAPIView, RegisterAPIView, RefreshTokenAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='user-register'),
    path('login/', LoginAPIView.as_view(), name='user-login'),
    path('refresh/', RefreshTokenAPIView.as_view(), name='user-refresh'),
]