import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import split_audio_by_reference


class ParseArgsTests(unittest.TestCase):
    def test_parse_multiple_references(self) -> None:
        args = split_audio_by_reference.parse_args(
            [
                "--input",
                "story.mp3",
                "--reference",
                "intro.mp3",
                "--reference",
                "divider.mp3",
                "--output",
                "chapters",
                "--min-distance",
                "5",
            ]
        )

        self.assertEqual(args.input, "story.mp3")
        self.assertEqual(args.reference, ["intro.mp3", "divider.mp3"])
        self.assertEqual(args.output, "chapters")
        self.assertEqual(args.min_distance, 5.0)


class ValidateEnvironmentTests(unittest.TestCase):
    @mock.patch("split_audio_by_reference.shutil.which", return_value="ffmpeg")
    def test_validate_environment_accepts_existing_files(self, _which: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / "story.mp3"
            reference_file = temp_path / "divider.mp3"
            input_file.write_bytes(b"input")
            reference_file.write_bytes(b"ref")

            args = SimpleNamespace(
                input=str(input_file),
                reference=[str(reference_file)],
                min_distance=3.0,
                hop_length=512,
                threshold_scale=0.9,
            )

            split_audio_by_reference.validate_environment(args)

    @mock.patch("split_audio_by_reference.shutil.which", return_value=None)
    def test_validate_environment_requires_ffmpeg(self, _which: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / "story.mp3"
            reference_file = temp_path / "divider.mp3"
            input_file.write_bytes(b"input")
            reference_file.write_bytes(b"ref")

            args = SimpleNamespace(
                input=str(input_file),
                reference=[str(reference_file)],
                min_distance=3.0,
                hop_length=512,
                threshold_scale=0.9,
            )

            with self.assertRaises(split_audio_by_reference.ConfigurationError):
                split_audio_by_reference.validate_environment(args)

    @mock.patch("split_audio_by_reference.shutil.which", return_value="ffmpeg")
    def test_validate_environment_requires_existing_reference_files(
        self, _which: mock.Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / "story.mp3"
            input_file.write_bytes(b"input")

            args = SimpleNamespace(
                input=str(input_file),
                reference=[str(temp_path / "missing.mp3")],
                min_distance=3.0,
                hop_length=512,
                threshold_scale=0.9,
            )

            with self.assertRaises(split_audio_by_reference.ConfigurationError):
                split_audio_by_reference.validate_environment(args)


if __name__ == "__main__":
    unittest.main()
