from django.db import models
from django.conf import settings

class StaticCamera(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ip_address = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    stream_url = models.CharField(max_length=255, blank=True, null=True)

    def rtsp_url(self):
        return f"rtsp://{self.username}:{self.password}@{self.ip_address}:554/Streaming/Channels/101"

class DDNSCamera(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ddns_hostname = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    stream_url = models.CharField(max_length=255, blank=True, null=True)

    def rtsp_url(self):
        return f"rtsp://{self.username}:{self.password}@{self.ddns_hostname}:554/Streaming/Channels/101"
