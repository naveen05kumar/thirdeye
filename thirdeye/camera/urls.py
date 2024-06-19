from django.urls import path
from .views import StaticCameraView, DDNSCameraView, GetStreamURLView, GenerateStreamURLView

urlpatterns = [
    path('static-camera/', StaticCameraView.as_view(), name='static-camera'),
    path('ddns-camera/', DDNSCameraView.as_view(), name='ddns-camera'),
    path('get-stream-url/<str:camera_type>/', GetStreamURLView.as_view(), name='get-stream-url'),
    path('generate-stream-url/', GenerateStreamURLView.as_view(), name='generate-stream-url'),
]
