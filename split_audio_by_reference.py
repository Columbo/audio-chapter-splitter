from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import time
from importlib import import_module
from pathlib import Path


DEFAULT_OUTPUT_DIR = "kapitel_ref"
DEFAULT_MIN_DISTANCE = 3.0
DEFAULT_HOP_LENGTH = 512
DEFAULT_THRESHOLD_SCALE = 0.9
DEFAULT_OUTPUT_FORMAT = "mp3"
WAV_EXTENSIONS = {".wav", ".wave"}
__version__ = "0.2.0"


class ConfigurationError(Exception):
    """Raised when the CLI configuration is invalid for the current system."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Split a long audio file into chapter files by detecting repeated "
            "reference audio clips."
        )
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the main audio file, for example hoerspiel.mp3.",
    )
    parser.add_argument(
        "--reference",
        action="append",
        required=True,
        help=(
            "Path to a reference clip that marks chapter boundaries. "
            "Repeat this option for multiple reference files."
        ),
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for exported chapter files. Default: {DEFAULT_OUTPUT_DIR}.",
    )
    parser.add_argument(
        "--output-format",
        default=DEFAULT_OUTPUT_FORMAT,
        choices=("mp3", "wav"),
        help=(
            "Audio format for exported chapter files. "
            f"Default: {DEFAULT_OUTPUT_FORMAT}."
        ),
    )
    parser.add_argument(
        "--min-distance",
        type=float,
        default=DEFAULT_MIN_DISTANCE,
        help=(
            "Minimum number of seconds between detected chapter markers. "
            f"Default: {DEFAULT_MIN_DISTANCE}."
        ),
    )
    parser.add_argument(
        "--hop-length",
        type=int,
        default=DEFAULT_HOP_LENGTH,
        help=f"Hop length for chroma analysis. Default: {DEFAULT_HOP_LENGTH}.",
    )
    parser.add_argument(
        "--threshold-scale",
        type=float,
        default=DEFAULT_THRESHOLD_SCALE,
        help=(
            "Scale factor applied to the dynamic self-similarity threshold. "
            f"Default: {DEFAULT_THRESHOLD_SCALE}."
        ),
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary WAV file for debugging.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def validate_environment(args: argparse.Namespace) -> None:
    if args.min_distance < 0:
        raise ConfigurationError("--min-distance must be zero or greater.")
    if args.hop_length <= 0:
        raise ConfigurationError("--hop-length must be greater than zero.")
    if args.threshold_scale <= 0:
        raise ConfigurationError("--threshold-scale must be greater than zero.")

    input_path = Path(args.input)
    if not input_path.is_file():
        raise ConfigurationError(f"Input audio file not found: {input_path}")

    missing_references = [ref for ref in args.reference if not Path(ref).is_file()]
    if missing_references:
        missing = ", ".join(missing_references)
        raise ConfigurationError(f"Reference audio file(s) not found: {missing}")

    if requires_ffmpeg(args) and shutil.which("ffmpeg") is None:
        raise ConfigurationError(
            "ffmpeg is not available on PATH. Install ffmpeg and try again."
        )


def requires_ffmpeg(args: argparse.Namespace) -> bool:
    if args.output_format.lower() not in {"wav"}:
        return True

    all_input_files = [args.input, *args.reference]
    return any(Path(file_path).suffix.lower() not in WAV_EXTENSIONS for file_path in all_input_files)


def print_progress_eta(index: int, total: int, start_time: float, bar_length: int = 40) -> None:
    fraction = index / total if total else 1.0
    arrow = "#" * int(fraction * bar_length)
    spaces = "-" * (bar_length - len(arrow))
    elapsed = time.time() - start_time
    eta = elapsed / fraction - elapsed if fraction > 0 else 0
    sys.stdout.write(
        f"\rProgress: [{arrow}{spaces}] {int(fraction * 100)}% ETA: {int(eta)}s"
    )
    sys.stdout.flush()


def load_reference_data(
    reference_files: list[str],
    sample_rate: int,
    hop_length: int,
    threshold_scale: float,
) -> tuple[list[object], list[float]]:
    librosa = import_module("librosa")
    np = import_module("numpy")

    reference_chromas: list[object] = []
    reference_thresholds: list[float] = []

    for ref_file in reference_files:
        y_ref, _ = librosa.load(ref_file, sr=sample_rate)
        chroma_ref = librosa.feature.chroma_stft(
            y=y_ref,
            sr=sample_rate,
            hop_length=hop_length,
        )
        chroma_ref = chroma_ref / (
            np.linalg.norm(chroma_ref, axis=0, keepdims=True) + 1e-8
        )
        reference_chromas.append(chroma_ref)

        self_similarity = np.mean(np.diag(np.dot(chroma_ref.T, chroma_ref)))
        reference_thresholds.append(self_similarity * threshold_scale)

    return reference_chromas, reference_thresholds


def detect_chapter_times(
    chroma: object,
    sample_rate: int,
    reference_chromas: list[object],
    reference_thresholds: list[float],
    hop_length: int,
    min_distance_between_chapters: float,
) -> list[float]:
    librosa = import_module("librosa")
    np = import_module("numpy")

    chapter_times: list[float] = []
    n_frames = chroma.shape[1]
    start_time = time.time()
    index = 0

    while index < n_frames:
        matched = False
        for chroma_ref, threshold in zip(reference_chromas, reference_thresholds):
            ref_len = chroma_ref.shape[1]
            if index + ref_len > n_frames:
                continue

            window = chroma[:, index : index + ref_len]
            similarity = np.mean(np.sum(window * chroma_ref, axis=0))

            if similarity > threshold:
                time_sec = librosa.frames_to_time(
                    index,
                    sr=sample_rate,
                    hop_length=hop_length,
                )
                if (
                    not chapter_times
                    or time_sec - chapter_times[-1] > min_distance_between_chapters
                ):
                    chapter_times.append(time_sec)
                index += ref_len
                matched = True
                break

        if not matched:
            index += 1

        if index % 500 == 0 or index >= n_frames - 1:
            print_progress_eta(index + 1, n_frames, start_time)

    print()
    return chapter_times


def export_chapters(
    audio: object,
    output_dir: Path,
    chapter_times: list[float],
    duration: float,
    output_format: str,
) -> None:
    chapter_boundaries = [0.0] + sorted(chapter_times) + [duration]
    output_dir.mkdir(parents=True, exist_ok=True)

    if not chapter_times:
        print(
            "No chapter markers detected. Exporting the full audio as a single file.",
            file=sys.stderr,
        )

    for idx in range(len(chapter_boundaries) - 1):
        start_ms = int(chapter_boundaries[idx] * 1000)
        end_ms = int(chapter_boundaries[idx + 1] * 1000)
        segment = audio[start_ms:end_ms]
        filename = output_dir / f"kapitel_{idx + 1}.{output_format}"
        segment.export(filename, format=output_format)
        print(f"Saved chapter {idx + 1}: {filename}")


def split_audio(args: argparse.Namespace) -> None:
    temp_wav_path: Path | None = None
    try:
        librosa = import_module("librosa")
        np = import_module("numpy")
        pydub = import_module("pydub")
        CouldntDecodeError = import_module("pydub.exceptions").CouldntDecodeError
    except ModuleNotFoundError as exc:
        raise ConfigurationError(
            "Missing Python dependency. Install the packages from requirements.txt "
            "and try again."
        ) from exc

    try:
        audio = pydub.AudioSegment.from_file(args.input)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_wav_path = Path(temp_file.name)

        audio.export(temp_wav_path, format="wav")

        y, sample_rate = librosa.load(temp_wav_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sample_rate)

        reference_chromas, reference_thresholds = load_reference_data(
            reference_files=args.reference,
            sample_rate=sample_rate,
            hop_length=args.hop_length,
            threshold_scale=args.threshold_scale,
        )

        chroma = librosa.feature.chroma_stft(
            y=y,
            sr=sample_rate,
            hop_length=args.hop_length,
        )
        chroma = chroma / (np.linalg.norm(chroma, axis=0, keepdims=True) + 1e-8)

        chapter_times = detect_chapter_times(
            chroma=chroma,
            sample_rate=sample_rate,
            reference_chromas=reference_chromas,
            reference_thresholds=reference_thresholds,
            hop_length=args.hop_length,
            min_distance_between_chapters=args.min_distance,
        )

        export_chapters(
            audio=audio,
            output_dir=Path(args.output),
            chapter_times=chapter_times,
            duration=duration,
            output_format=args.output_format,
        )
    except CouldntDecodeError as exc:
        raise ConfigurationError(
            "Could not decode one of the audio files. Confirm the input and reference "
            "files are valid audio files and ffmpeg is installed."
        ) from exc
    finally:
        if temp_wav_path and temp_wav_path.exists() and not args.keep_temp:
            temp_wav_path.unlink()


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        validate_environment(args)
        split_audio(args)
        return 0
    except ConfigurationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
