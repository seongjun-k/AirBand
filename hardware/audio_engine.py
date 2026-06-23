# hardware/audio_engine.py
import pygame
import numpy as np
from config import AUDIO_FREQUENCY, AUDIO_CHANNELS, AUDIO_BUFFER, NOTE_DURATION

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def note_to_freq(note: str, octave: int) -> float:
    """A4=440Hz 기준 음이름 + 옥타브 -> 주파수(Hz) 변환"""
    semitone = NOTE_NAMES.index(note) + (octave - 4) * 12 - 9
    return 440.0 * (2 ** (semitone / 12))


class AudioEngine:
    """
    pygame.mixer 기반 오디오 엔진.
    테레민 합성음 및 드럼 합성음을 실시간 재생.
    """

    def __init__(self):
        pygame.mixer.pre_init(AUDIO_FREQUENCY, -16, AUDIO_CHANNELS, AUDIO_BUFFER)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)  # 동시 채널 수를 32개로 늘림
        self.master_volume = 0.7
        self._active_sounds = []  # 가비지 컬렉터에 의해 소리가 끊기는 현상 방지용 참조 보관 리스트

    def play_theremin(self, note: str, octave: int, volume: float = 0.5):
        freq    = note_to_freq(note, octave)
        vol     = self.master_volume * volume
        samples = self._synth_theremin(freq, NOTE_DURATION, vol)
        sound = pygame.sndarray.make_sound(samples)
        sound.play()
        self._keep_alive(sound)

    def play_piano(self, note: str, octave: int, volume: float = 0.5):
        freq    = note_to_freq(note, octave)
        vol     = self.master_volume * volume
        samples = self._synth_piano(freq, NOTE_DURATION, vol)
        sound = pygame.sndarray.make_sound(samples)
        sound.play()
        self._keep_alive(sound)

    def play_drum(self, pad: str, velocity: float = 0.5):
        vol = self.master_volume * velocity
        synth_map = {
            'kick':  self._synth_kick,
            'snare': self._synth_snare,
            'hihat': self._synth_hihat,
            'clap':  self._synth_clap,
        }
        fn = synth_map.get(pad)
        if fn:
            sound = pygame.sndarray.make_sound(fn(vol))
            sound.play()
            self._keep_alive(sound)

    def _keep_alive(self, sound):
        self._active_sounds.append(sound)
        if len(self._active_sounds) > 32:
            self._active_sounds.pop(0)

    def set_volume(self, volume: float):
        """volume: 0~100 사이 값"""
        self.master_volume = max(0.0, min(1.0, volume / 100.0))

    def _synth_piano(self, freq: float, duration: float, vol: float) -> np.ndarray:
        """피아노 특유의 타격형 배음 합성 및 빠른 엔벨롭 감쇠"""
        sr = AUDIO_FREQUENCY
        t  = np.linspace(0, duration, int(sr * duration), False)
        wave = (
            np.sin(2 * np.pi * freq * t) * 0.6 +
            np.sin(2 * np.pi * freq * 2 * t) * 0.3 +
            np.sin(2 * np.pi * freq * 3 * t) * 0.1
        )
        envelope = np.exp(-t * 6)
        wave = (wave * envelope * vol * 32767).astype(np.int16)
        return np.column_stack([wave, wave])

    def _synth_theremin(self, freq: float, duration: float, vol: float) -> np.ndarray:
        """테레민 특유의 사인파 + 약한 비브라토 + 부드러운 엔벨롭 합성"""
        sr = AUDIO_FREQUENCY
        t  = np.linspace(0, duration, int(sr * duration), False)
        
        # 6Hz의 미세한 비브라토 추가 (테레민 풍의 음정 흔들림)
        vibrato = 1.0 + 0.01 * np.sin(2 * np.pi * 6.0 * t)
        phase = 2 * np.pi * freq * t * vibrato
        
        # 순수 사인파에 가까우나 따뜻함을 위해 미세한 2차 배음 추가
        wave = np.sin(phase) * 0.95 + np.sin(2 * phase) * 0.05
        
        # 너무 툭 끊어지지 않고 부드럽게 감쇠하는 엔벨롭 (테레민 특성 반영)
        envelope = np.exp(-t * 4)
        wave = (wave * envelope * vol * 32767).astype(np.int16)
        return np.column_stack([wave, wave])

    def _synth_kick(self, vol: float) -> np.ndarray:
        sr, dur = AUDIO_FREQUENCY, 0.35
        t = np.linspace(0, dur, int(sr * dur), False)
        freq_env = 150 * np.exp(-t * 20) + 50
        wave = np.sin(2 * np.pi * np.cumsum(freq_env) / sr)
        wave = (wave * np.exp(-t * 8) * vol * 32767).astype(np.int16)
        return np.column_stack([wave, wave])

    def _synth_snare(self, vol: float) -> np.ndarray:
        sr, dur = AUDIO_FREQUENCY, 0.2
        t = np.linspace(0, dur, int(sr * dur), False)
        noise = np.random.uniform(-1, 1, len(t))
        env   = np.exp(-t * 15) * (1 - t / dur) ** 1.5
        wave  = (noise * env * vol * 32767).astype(np.int16)
        return np.column_stack([wave, wave])

    def _synth_hihat(self, vol: float) -> np.ndarray:
        sr, dur = AUDIO_FREQUENCY, 0.1
        t = np.linspace(0, dur, int(sr * dur), False)
        noise = np.random.uniform(-1, 1, len(t))
        wave  = (noise * np.exp(-t * 40) * vol * 0.6 * 32767).astype(np.int16)
        return np.column_stack([wave, wave])

    def _synth_clap(self, vol: float) -> np.ndarray:
        sr    = AUDIO_FREQUENCY
        total = np.zeros(int(sr * 0.15))
        for offset_ms in [0, 12, 24]:
            dur  = 0.05
            t    = np.linspace(0, dur, int(sr * dur), False)
            burst = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 25)
            start = int(offset_ms / 1000 * sr)
            total[start:start + len(burst)] += burst
        wave = (total * vol * 0.7 * 32767).astype(np.int16)
        return np.column_stack([wave, wave])

    def close(self):
        pygame.mixer.quit()
