# scratch/test_cam_fps.py
import cv2
import time
import sys

def test_fps(use_mjpg=False, use_buffer_1=False, remove_sleep=False):
    print(f"\n--- Testing: MJPG={use_mjpg}, BufferSize1={use_buffer_1}, RemoveSleep={remove_sleep} ---")
    cap = cv2.VideoCapture(0)
    
    if use_mjpg:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    if use_buffer_1:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
    if not cap.isOpened():
        print("Error: Could not open video device.")
        return

    start_time = time.time()
    frames = 0
    test_duration = 3.0  # 3 seconds test
    
    while time.time() - start_time < test_duration:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        frames += 1
        
        # Check frame shape
        if frames == 1:
            print(f"Initial frame shape: {frame.shape}, ndim: {frame.ndim}")
            
        if not remove_sleep:
            time.sleep(0.015)
            
    end_time = time.time()
    elapsed = end_time - start_time
    fps = frames / elapsed
    print(f"Result: Captured {frames} frames in {elapsed:.2f} seconds. FPS: {fps:.2f}")
    cap.release()

if __name__ == "__main__":
    # Test combinations
    # 1. Baseline
    test_fps(use_mjpg=False, use_buffer_1=False, remove_sleep=False)
    # 2. Remove sleep
    test_fps(use_mjpg=False, use_buffer_1=False, remove_sleep=True)
    # 3. Add Buffer=1 and Remove sleep
    test_fps(use_mjpg=False, use_buffer_1=True, remove_sleep=True)
    # 4. Add MJPG, Buffer=1, Remove sleep
    test_fps(use_mjpg=True, use_buffer_1=True, remove_sleep=True)
