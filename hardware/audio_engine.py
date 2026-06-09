# hardware/audio_engine.py
import pygame
import numpy as np
from config import AUDIO_FREQUENCY, AUDIO_CHANNELS, AUDIO_BUFFER, NOTE_DURATION

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def note_to_freq(note: str, octave: int) -> float:
    """A4=440Hz 기준으로 음계 이름 + 옷타브 → 주파수(Hz) 변환"""
    semitone = NOTE_NAMES.index(note) + (octave - 4) * 12 - 9
    return 440.0 * (2 ** (semitone / 12))


class AudioEngine:
    """
    pygame.mixer 기반 오디오 엔진.
    피아노 음(사인파 합성)과 드럼 타격음(노이즈 합성) 재생.
    """

    def __init__(self):
        pygame.mixer.pre_init(AUDIO_FREQUENCY, -16, AUDIO_CHANNELS, AUDIO_BUFFER)
        pygame.mixer.init()
        self.master_volume = 0.7

    def play_piano(self, note: str, octave: int, volume: float = 0.5):
        freq    = note_to_freq(note, octave)
        vol     = self.master_volume * volume
        samples = self._synth_piano(freq, NOTE_DURATION, vol)
        pygame.sndarray.make_sound(samples).play()

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
            pygame.sndarray.make_sound(fn(vol)).play()

    def set_volume(self, volume: float):
        """volume: 0~100 정수"""
        self.master_volume = max(0.0, min(1.0, volume / 100.0))

    # ── 합성 함수들 ──
    def _synth_piano(self, freq: float, duration: float, vol: float) -> np.ndarray:
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
