# camera/consumers.py

import cv2
import numpy as np
from channels.generic.websocket import WebsocketConsumer
import threading

class CameraConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.camera_url = self.scope['url_route']['kwargs']['camera_url']
        self.capture_thread = threading.Thread(target=self.stream_camera)
        self.capture_thread.start()

    def disconnect(self, close_code):
        self.capture_thread.join()

    def stream_camera(self):
        cap = cv2.VideoCapture(self.camera_url)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode('.jpg', frame)
            self.send(buffer.tobytes())
        cap.release()
