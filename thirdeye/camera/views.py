from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import StaticCamera, DDNSCamera
from .serializers import StaticCameraSerializer, DDNSCameraSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

class StaticCameraView(generics.GenericAPIView):
    serializer_class = StaticCameraSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=StaticCameraSerializer)
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            StaticCamera.objects.update_or_create(user=request.user, defaults=serializer.validated_data)
            return Response({"message": "Static camera details saved successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DDNSCameraView(generics.GenericAPIView):
    serializer_class = DDNSCameraSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=DDNSCameraSerializer)
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            DDNSCamera.objects.update_or_create(user=request.user, defaults=serializer.validated_data)
            return Response({"message": "DDNS camera details saved successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetStreamURLView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, camera_type):
        try:
            if camera_type == 'static':
                camera = StaticCamera.objects.get(user=request.user)
            else:
                camera = DDNSCamera.objects.get(user=request.user)
            if not camera.stream_url:
                camera.stream_url = camera.rtsp_url()
                camera.save()
            return Response({"stream_url": camera.stream_url}, status=status.HTTP_200_OK)
        except (StaticCamera.DoesNotExist, DDNSCamera.DoesNotExist):
            return Response({"error": "Camera not found"}, status=status.HTTP_404_NOT_FOUND)

class GenerateStreamURLView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        camera_type = request.data.get('camera_type')
        if not camera_type:
            return Response({"error": "camera_type is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if camera_type == 'static':
                camera = StaticCamera.objects.get(user=request.user)
            elif camera_type == 'ddns':
                camera = DDNSCamera.objects.get(user=request.user)
            else:
                return Response({"error": "Invalid camera_type"}, status=status.HTTP_400_BAD_REQUEST)
            
            camera.stream_url = camera.rtsp_url()
            camera.save()
            return Response({"stream_url": camera.stream_url}, status=status.HTTP_200_OK)
        except (StaticCamera.DoesNotExist, DDNSCamera.DoesNotExist):
            return Response({"error": "Camera not found"}, status=status.HTTP_404_NOT_FOUND)
