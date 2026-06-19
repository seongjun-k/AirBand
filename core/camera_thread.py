# core/camera_thread.py
import cv2
import time
import math
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from core.hand_tracker import HandTracker
from config import CAM_WIDTH, CAM_HEIGHT, CAM_FPS, CAMERA_INDEX

class InferenceThread(QThread):
    """
    손 트래킹 추론을 백그라운드에서 실행하는 비동기 스레드
    """
    result_ready = pyqtSignal(object, object)

    def __init__(self, tracker):
        super().__init__()
        self._tracker = tracker
        self.running = False
        self._frame = None
        self._mutex = QMutex()

    def set_frame(self, frame):
        self._mutex.lock()
        # 이전 프레임이 대기 중이더라도 최신 프레임으로 덮어씀 (Frame Drop 기법으로 레이턴시 최소화)
        self._frame = frame.copy() if frame is not None else None
        self._mutex.unlock()

    def run(self):
        self.running = True
        while self.running:
            self._mutex.lock()
            local_frame = self._frame
            self._frame = None  # 한 번 가져온 프레임은 비움
            self._mutex.unlock()

            if local_frame is not None:
                results, fingertips = self._tracker.process(local_frame)
                self.result_ready.emit(results, fingertips)
            else:
                time.sleep(0.005)  # CPU 점유율 과다 방지

    def stop(self):
        self.running = False
        self.wait()


class CameraThread(QThread):
    """
    OpenCV 비디오 캡처 전용 스레드.
    추론 스레드(InferenceThread)를 내부에 탑재하여 비동기로 구동.
    화면 갱신은 지연 없이 카메라 고유 FPS(30 FPS)로 부드럽게 방출됨.
    """
    frame_ready = pyqtSignal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self._tracker = None
        self._inf_thread = None
        
        self._latest_results = None
        self._latest_fingertips = []
        self._result_mutex = QMutex()

    def run(self):
        self._tracker = HandTracker()
        self._inf_thread = InferenceThread(self._tracker)
        self._inf_thread.result_ready.connect(self._on_inference_done)
        self._inf_thread.start()
        
        cap = cv2.VideoCapture(CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, CAM_FPS)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 버퍼 크기 최소화하여 레이턴시 차단
        self.running = True

        while self.running:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            # libcamerify/libcamera 복원 로직
            if frame.ndim == 2 and frame.shape[0] == 1:
                total_elements = frame.shape[1]
                if total_elements == 921600:
                    frame = frame.reshape((480, 640, 3))
                elif total_elements == 230400:
                    frame = frame.reshape((240, 320, 3))
                elif total_elements == 460800:
                    frame = frame.reshape((240, 640, 3))
                    frame = frame[:, :320, :]
                elif total_elements == 115200:
                    frame = frame.reshape((120, 320, 3))
                else:
                    h = int(math.sqrt(total_elements / 4))
                    w = int(h * 4 / 3)
                    if w * h * 3 == total_elements:
                        frame = frame.reshape((h, w, 3))
                    else:
                        continue

            # 거울 모드 + 상하 반전 (180도 회전) 적용
            frame = cv2.flip(frame, -1)

            # 비동기 추론 스레드에 최신 프레임 전달
            self._inf_thread.set_frame(frame)

            # 캐시된 가장 최신의 랜드마크 좌표 가져오기
            self._result_mutex.lock()
            res = self._latest_results
            tips = self._latest_fingertips
            self._result_mutex.unlock()

            # 원본 BGR 프레임에 최신 랜드마크 드로잉
            annotated = self._tracker.draw_landmarks(frame, res)
            
            # 백그라운드 스레드에서 미리 RGB 변환 및 640x480으로 스케일업 수행 (GUI 스레드 부하 분산)
            rgb_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            resized_rgb = cv2.resize(rgb_frame, (640, 480), interpolation=cv2.INTER_NEAREST)
            
            # UI로 즉시 emit
            self.frame_ready.emit(resized_rgb, tips)
            
            # CPU 과다 점유를 방지하고 OS 스케줄러가 다른 스레드에 GIL을 양보할 수 있도록 미세 대기
            time.sleep(0.001)

        cap.release()
        
        if self._inf_thread:
            self._inf_thread.stop()
        if self._tracker:
            self._tracker.close()

    def _on_inference_done(self, results, fingertips):
        self._result_mutex.lock()
        self._latest_results = results
        self._latest_fingertips = fingertips
        self._result_mutex.unlock()

    def stop(self):
        self.running = False
        self.wait()
