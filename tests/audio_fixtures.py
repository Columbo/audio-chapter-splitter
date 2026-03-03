import math
import struct
import wave
from pathlib import Path


SAMPLE_RATE = 22050


def _tone_frames(
    duration_seconds: float,
    *,
    frequency: float = 440.0,
    amplitude: int = 12000,
    sample_rate: int = SAMPLE_RATE,
) -> bytes:
    frame_count = int(duration_seconds * sample_rate)
    frames = bytearray()

    for index in range(frame_count):
        sample = int(
            amplitude
            * math.sin((2.0 * math.pi * frequency * index) / sample_rate)
        )
        frames.extend(struct.pack("<h", sample))

    return bytes(frames)


def _silence_frames(duration_seconds: float, *, sample_rate: int = SAMPLE_RATE) -> bytes:
    frame_count = int(duration_seconds * sample_rate)
    return b"\x00\x00" * frame_count


def _write_wav(path: Path, frames: bytes, *, sample_rate: int = SAMPLE_RATE) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)


def create_sample_audio_fixture(base_dir: Path) -> tuple[Path, Path]:
    reference_path = base_dir / "divider.wav"
    story_path = base_dir / "story.wav"

    reference_frames = _tone_frames(0.8)
    story_frames = b"".join(
        [
            _silence_frames(1.0),
            reference_frames,
            _silence_frames(1.0),
            reference_frames,
            _silence_frames(1.0),
        ]
    )

    _write_wav(reference_path, reference_frames)
    _write_wav(story_path, story_frames)

    return story_path, reference_path
