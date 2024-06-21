from rest_framework import generics, status, views
from rest_framework.response import Response
from .models import User
from .serializers import (
    RegisterSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    RequestPasswordResetEmailSerializer,
    SetNewPasswordWithOTPSerializer
)
from .utils import Util, generate_otp
from datetime import datetime, timedelta
import random
import string
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.cache import cache
from django.utils import timezone


logger = logging.getLogger(__name__)

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        user_data = request.data.copy()  # Create a mutable copy of the request data
        serializer = self.serializer_class(data=user_data)
        serializer.is_valid(raise_exception=True)

        verification_code = ''.join(random.choices(string.digits, k=6))
        user_data['verification_code'] = verification_code
        user_data['verification_code_expires_at'] = (timezone.now() + timedelta(minutes=10)).isoformat()

        try:
            cache.set(verification_code, user_data, timeout=600)  # Cache for 10 minutes

            email_body = f'Hi {user_data["username"]}, use the verification code below to verify your email address:\n{verification_code}'
            data = {
                'email_body': email_body,
                'to_email': user_data['email'],
                'email_subject': 'Verify Your Email'
            }

            Util.send_email(data)
        except Exception as e:
            logger.error(f"Error in registration process: {e}")
            return Response({'error': 'An error occurred. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': 'Verification code sent to your email'}, status=status.HTTP_201_CREATED)
class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    @swagger_auto_schema(
        request_body=EmailVerificationSerializer,
        responses={
            200: openapi.Response('Email successfully verified', EmailVerificationSerializer),
            400: 'Invalid or expired verification code',
            500: 'Internal server error'
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data.get('code')
        user_data = cache.get(code)

        if not user_data:
            return Response({'error': 'Invalid or expired verification code'}, status=status.HTTP_400_BAD_REQUEST)

        if datetime.fromisoformat(user_data['verification_code_expires_at']) < datetime.now():
            cache.delete(code)  # Clear the expired cached data
            return Response({'error': 'Verification code has expired'}, status=status.HTTP_400_BAD_REQUEST)

        # Remove sensitive fields before saving
        user_data.pop('verification_code')
        user_data.pop('verification_code_expires_at')

        user = User(
            email=user_data['email'],
            username=user_data['username']
        )
        user.set_password(user_data['password'])
        user.is_active = True  # Activate user
        user.is_verified = True  # Mark user as verified
        user.save()
        cache.delete(code)  # Clear the cached data

        email_body = f'Hi {user.username}, your email has been successfully verified. You can now log in.'
        data = {
            'email_body': email_body,
            'to_email': user.email,
            'email_subject': 'Email Verified'
        }
        Util.send_email(data)

        return Response({'detail': 'Email successfully verified'}, status=status.HTTP_200_OK)

class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = RequestPasswordResetEmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()
        
        email_body = f'Hello, \n Use the OTP below to reset your password \n{otp}'
        data = {'email_body': email_body, 'to_email': user.email, 'email_subject': 'Reset your password'}
        Util.send_email(data)
        
        return Response({'success': 'OTP has been sent to your email'}, status=status.HTTP_200_OK)

class SetNewPasswordWithOTP(generics.GenericAPIView):
    serializer_class = SetNewPasswordWithOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': 'Password reset successful'}, status=status.HTTP_200_OK)
