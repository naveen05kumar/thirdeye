from datetime import datetime, timedelta
from django.utils import timezone
import random
import string
import logging
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
from .utils import Util, generate_otp, google_authenticate, is_otp_valid
from camera.models import CameraStream
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.cache import cache

logger = logging.getLogger(__name__)

class GoogleSignInView(views.APIView):
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = google_authenticate(token)
        if not user:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
        tokens = user.tokens()
        streams = CameraStream.objects.filter(user=user)
        stream_urls = [stream.stream_url for stream in streams]
        
        email_body = f'Hello {user.username},\n\nWelcome to our service! Your email has been successfully used to sign in with Google.'
        data = {
            'email_body': email_body,
            'to_email': user.email,
            'email_subject': 'Welcome to Our Service'
        }
        Util.send_email(data)
        
        return Response({
            'user_info': {
                'username': user.username,
                'email': user.email,
            },
            'access_token': tokens['access'],
            'refresh_token': tokens['refresh'],
            'stream_urls': stream_urls,
        }, status=status.HTTP_200_OK)

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        user_data = request.data.copy()
        serializer = self.serializer_class(data=user_data)
        serializer.is_valid(raise_exception=True)

        verification_code = ''.join(random.choices(string.digits, k=6))
        user_data['verification_code'] = verification_code
        user_data['verification_code_expires_at'] = (timezone.now() + timedelta(minutes=10)).isoformat()

        try:
            cache.set(verification_code, user_data, timeout=600)

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
        logger.debug('Received request data: %s', request.data)
        
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            logger.error('Validation errors: %s', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data.get('code')
        user_data = cache.get(code)

        if not user_data:
            logger.error('Invalid or expired verification code: %s', code)
            return Response({'error': 'Invalid or expired verification code'}, status=status.HTTP_400_BAD_REQUEST)

        verification_code_expires_at = datetime.fromisoformat(user_data['verification_code_expires_at']).replace(tzinfo=timezone.utc)
        current_time = timezone.now()

        if current_time > verification_code_expires_at:
            logger.error('Verification code has expired for code: %s', code)
            return Response({'error': 'Verification code has expired'}, status=status.HTTP_400_BAD_REQUEST)

        user_data.pop('verification_code')
        user_data.pop('verification_code_expires_at')

        serializer = RegisterSerializer(data=user_data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_verified = True
            user.save()

            logger.debug('User created and email verified: %s', user.username)

            return Response({'detail': 'Email successfully verified'}, status=status.HTTP_200_OK)
        else:
            logger.error('Error creating user: %s', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Retrieve all stream URLs for the user
        streams = CameraStream.objects.filter(user=user)
        stream_urls = [stream.stream_url for stream in streams]

        return Response({
            'user_info': {
                'username': user.username,
                'email': user.email,
            },
            'access_token': str(serializer.validated_data['tokens']['access']),
            'refresh_token': str(serializer.validated_data['tokens']['refresh']),
            'stream_urls': stream_urls,
        }, status=status.HTTP_200_OK)
    
class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = RequestPasswordResetEmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        otp_request_count = cache.get(f'otp_requests_{email}', 0)
        first_request_time = cache.get(f'first_otp_request_{email}', None)
        
        if first_request_time and timezone.now() > first_request_time + timedelta(hours=1):
            cache.set(f'otp_requests_{email}', 0)
            otp_request_count = 0
            cache.set(f'first_otp_request_{email}', timezone.now())

        if otp_request_count >= 6:
            return Response({'error': 'Too many OTP requests. Please try again after 1 hours.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        otp = generate_otp()

        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        email_body = f'Hi {user.username}, use the OTP below to reset your password:\n{otp}'
        data = {
            'email_body': email_body,
            'to_email': user.email,
            'email_subject': 'Reset Your Password'
        }

        Util.send_email(data)
        
        cache.set(f'otp_requests_{email}', otp_request_count + 1)
        if not first_request_time:
            cache.set(f'first_otp_request_{email}', timezone.now())

        return Response({'detail': 'OTP sent to your email'}, status=status.HTTP_200_OK)

class SetNewPasswordWithOTPView(generics.GenericAPIView):
    serializer_class = SetNewPasswordWithOTPSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'detail': 'Password reset successful'}, status=status.HTTP_200_OK)
