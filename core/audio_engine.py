# core/audio_engine.py
"""
오디오 재생 엔진 모듈.

담당 기능:
  - pygame.mixer 초기화
  - 피아노 음 생성 및 재생 (numpy 사인파)
  - 드럼 사운드 파일 로드 및 재생
  - 전체 볼륨 조절

사용 예시:
    engine = AudioEngine()
    engine.play_piano('C', 4, 0.8)
    engine.play_drum('snare', 0.9)
    engine.set_volume(70)   # 0~100
    engine.close()
"""
import numpy as np
import pygame
from config import (
    AUDIO_FREQUENCY, AUDIO_CHANNELS, AUDIO_BUFFER,
    NOTE_DURATION, SCALE_NOTES
)

# 음계 이름 → 반음(semitone) 오프셋 (C 기준)
_NOTE_SEMITONES = {
    'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
    'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
}


class AudioEngine:
    """pygame.mixer 기반 오디오 재생 엔진"""

    def __init__(self):
        pygame.mixer.pre_init(
            frequency=AUDIO_FREQUENCY,
            size=-16,
            channels=AUDIO_CHANNELS,
            buffer=AUDIO_BUFFER,
        )
        pygame.mixer.init()
        self._volume = 0.5  # 0.0 ~ 1.0
        self._drum_sounds: dict = {}   # pad_name → Sound
        self._load_drum_sounds()

    # ── 피아노 ────────────────────────────────────────────────

    def play_piano(self, note: str, octave: int, volume: float = 0.8):
        """
        사인파로 피아노 음 합성 후 재생.

        Parameters
        ----------
        note   : 음계 이름 ('C', 'D', ..., 'B')
        octave : 옥타브 (0~8)
        volume : 0.0~1.0 음량
        """
        freq = self._note_to_freq(note, octave)
        sound = self._synthesize(freq, NOTE_DURATION, volume * self._volume)
        sound.play()

    def _note_to_freq(self, note: str, octave: int) -> float:
        """음계 + 옥타브 → Hz (A4=440Hz 기준)"""
        semitone = _NOTE_SEMITONES.get(note, 0)
        # MIDI 번호: C4 = 60
        midi = (octave + 1) * 12 + semitone
        return 440.0 * (2 ** ((midi - 69) / 12))

    def _synthesize(self, freq: float, duration: float, amplitude: float) -> pygame.mixer.Sound:
        """사인파 버퍼 생성 → pygame.mixer.Sound 반환"""
        sr = AUDIO_FREQUENCY
        n_samples = int(sr * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        wave = (amplitude * 32767 * np.sin(2 * np.pi * freq * t)).astype(np.int16)
        stereo = np.column_stack([wave, wave])
        return pygame.sndarray.make_sound(stereo)

    # ── 드럼 ──────────────────────────────────────────────────

    def play_drum(self, pad: str, velocity: float = 0.8):
        """
        드럼 패드 사운드 재생.

        Parameters
        ----------
        pad      : 'hihat' | 'clap' | 'kick' | 'snare'
        velocity : 0.0~1.0 타격 세기
        """
        sound = self._drum_sounds.get(pad)
        if sound:
            sound.set_volume(velocity * self._volume)
            sound.play()

    def _load_drum_sounds(self):
        """
        assets/sounds/{pad}.wav 파일 로드.
        파일 없으면 해당 패드는 무시(무음).
        """
        import os
        pads = ['hihat', 'clap', 'kick', 'snare']
        for pad in pads:
            path = os.path.join('assets', 'sounds', f'{pad}.wav')
            if os.path.exists(path):
                self._drum_sounds[pad] = pygame.mixer.Sound(path)

    # ── 공통 제어 ─────────────────────────────────────────────

    def set_volume(self, volume_pct: int):
        """
        전체 볼륨 설정.

        Parameters
        ----------
        volume_pct : 0~100 정수
        """
        self._volume = max(0.0, min(1.0, volume_pct / 100))

    def get_volume_pct(self) -> int:
        """현재 볼륨 (0~100) 반환"""
        return int(self._volume * 100)

    def close(self):
        """pygame.mixer 종료"""
        pygame.mixer.quit()
