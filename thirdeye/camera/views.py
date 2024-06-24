# camera/views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import StaticCamera, DDNSCamera, CameraStream
from .serializers import StaticCameraSerializer, DDNSCameraSerializer, CameraStreamSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

class StaticCameraView(generics.GenericAPIView):
    serializer_class = StaticCameraSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=StaticCameraSerializer)
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            static_camera = StaticCamera.objects.create(user=request.user, **serializer.validated_data)
            CameraStream.objects.create(user=request.user, camera=static_camera, stream_url=static_camera.rtsp_url())
            return Response({"message": "Static camera details saved successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DDNSCameraView(generics.GenericAPIView):
    serializer_class = DDNSCameraSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=DDNSCameraSerializer)
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            ddns_camera = DDNSCamera.objects.create(user=request.user, **serializer.validated_data)
            CameraStream.objects.create(user=request.user, ddns_camera=ddns_camera, stream_url=ddns_camera.rtsp_url())
            return Response({"message": "DDNS camera details saved successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetStreamURLView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, camera_type):
        try:
            if camera_type == 'static':
                cameras = StaticCamera.objects.filter(user=request.user)
            else:
                cameras = DDNSCamera.objects.filter(user=request.user)
                
            stream_urls = []
            for camera in cameras:
                streams = CameraStream.objects.filter(user=request.user, camera=camera if camera_type == 'static' else None, ddns_camera=camera if camera_type != 'static' else None)
                for stream in streams:
                    stream_urls.append(stream.stream_url)
                    
            return Response({"stream_urls": stream_urls}, status=status.HTTP_200_OK)
        except (StaticCamera.DoesNotExist, DDNSCamera.DoesNotExist):
            return Response({"error": "Camera not found"}, status=status.HTTP_404_NOT_FOUND)
