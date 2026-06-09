# core/camera_thread.py
import cv2
from PyQt5.QtCore import QThread, pyqtSignal
from core.hand_tracker import HandTracker
from config import CAM_WIDTH, CAM_HEIGHT, CAM_FPS


class CameraThread(QThread):
    """
    OpenCV 캐트 + MediaPipe 추론을 별도 스레드에서 실행.
    결과는 frame_ready 시그널로 메인 스레드(UI)에 전달.

    Signals:
        frame_ready(np.ndarray, list): (BGR 프레임, fingertips 리스트)
    """
    frame_ready = pyqtSignal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self._tracker = HandTracker()

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, CAM_FPS)
        self.running = True

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            results, fingertips = self._tracker.process(frame)
            annotated = self._tracker.draw_landmarks(frame.copy(), results)
            self.frame_ready.emit(annotated, fingertips)

        cap.release()
        self._tracker.close()

    def stop(self):
        self.running = False
        self.wait()
