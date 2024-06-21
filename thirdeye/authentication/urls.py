from django.urls import path
from .views import RegisterView, VerifyEmail, LoginAPIView, RequestPasswordResetEmail, SetNewPasswordWithOTP

urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('email-verify/', VerifyEmail.as_view(), name="email-verify"),
    path('login/', LoginAPIView.as_view(), name="login"),
    path('request-reset-email/', RequestPasswordResetEmail.as_view(), name="request-reset-email"),
    path('set-new-password/', SetNewPasswordWithOTP.as_view(), name="set-new-password"),
]
