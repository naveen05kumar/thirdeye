# camera/urls.py

from django.urls import path
from .views import StaticCameraView, DDNSCameraView, GetStreamURLView

urlpatterns = [
    path('static-camera/', StaticCameraView.as_view(), name='static-camera'),
    path('ddns-camera/', DDNSCameraView.as_view(), name='ddns-camera'),
    path('get-stream-url/<str:camera_type>/', GetStreamURLView.as_view(), name='get-stream-url'),
]
