# core/gesture_detector.py
"""
제스처 감지 유틸리티 모듈.

담당 기능:
  - 손가락 펼침/접힘 판별
  - 핀치(엄지-검지 맞닿음) 판별
  - 손목 기준 상대 좌표 정규화
  - 두 손 모두 감지 여부 확인

모든 함수는 순수 함수(side-effect 없음)로 작성.
"""
from __future__ import annotations
import math
from typing import List, Dict, Tuple

# fingertips 인덱스 상수 (FINGERTIP_IDS 순서 기준)
THUMB  = 0
INDEX  = 1
MIDDLE = 2
RING   = 3
PINKY  = 4

# 핀치 판별 거리 임계값 (정규화 좌표 기준)
_PINCH_THRESHOLD = 0.07


def is_pinching(hand: Dict) -> bool:
    """
    엄지-검지 끝이 붙었으면(핀치 제스처) True.

    Parameters
    ----------
    hand : {'hand': str, 'tips': [(x,y,z)×5]}
    """
    tx, ty, _ = hand['tips'][THUMB]
    ix, iy, _ = hand['tips'][INDEX]
    dist = math.hypot(tx - ix, ty - iy)
    return dist < _PINCH_THRESHOLD


def count_extended_fingers(hand: Dict) -> int:
    """
    펼쳐진 손가락 수 반환 (엄지 제외, 검지~소지 4개 기준).

    Y 좌표 기준: 검지MCP(landmark 5)보다 위쪽이면 펼쳐진 것으로 간주.
    여기서는 tips 배열만 사용하므로, 인접 손가락 간 Y 비교로 근사.

    Note: 정확한 판별을 위해서는 MCP 관절 좌표가 필요하지만,
          여기서는 간이 방법(tips Y < 0.5 → 위쪽 = 펼침)을 사용.
    """
    tips = hand['tips']
    count = 0
    for i in (INDEX, MIDDLE, RING, PINKY):
        x, y, _ = tips[i]
        if y < 0.5:  # 화면 위쪽 절반이면 펼침으로 판단
            count += 1
    return count


def get_index_tip(hand: Dict) -> Tuple[float, float, float]:
    """
    검지 끝 좌표 (x, y, z) 반환.
    """
    return hand['tips'][INDEX]


def get_hand_center(hand: Dict) -> Tuple[float, float]:
    """
    5개 손가락 끝의 중심 좌표 반환.
    """
    xs = [t[0] for t in hand['tips']]
    ys = [t[1] for t in hand['tips']]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def both_hands_detected(fingertips: List[Dict]) -> bool:
    """양손(Left + Right) 모두 감지됐으면 True."""
    labels = {h['hand'] for h in fingertips}
    return 'Left' in labels and 'Right' in labels


def get_hand(fingertips: List[Dict], side: str = 'Left') -> Dict | None:
    """
    지정 손('Left' | 'Right') 데이터 반환. 없으면 None.
    """
    for h in fingertips:
        if h['hand'] == side:
            return h
    return None


def distance_2d(p1: Tuple, p2: Tuple) -> float:
    """두 점 사이 유클리드 거리 (x, y 만 사용)"""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
