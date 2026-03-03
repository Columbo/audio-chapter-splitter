import io
import importlib.util
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import split_audio_by_reference
from audio_fixtures import create_sample_audio_fixture


class IntegrationTests(unittest.TestCase):
    @unittest.skipUnless(
        all(
            importlib.util.find_spec(module_name) is not None
            for module_name in ("librosa", "numpy", "pydub")
        ),
        "audio runtime dependencies are not installed",
    )
    def test_cli_run_creates_multiple_wav_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            story_path, reference_path = create_sample_audio_fixture(base_dir)
            output_dir = base_dir / "chapters"

            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()

            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exit_code = split_audio_by_reference.main(
                    [
                        "--input",
                        str(story_path),
                        "--reference",
                        str(reference_path),
                        "--output",
                        str(output_dir),
                        "--output-format",
                        "wav",
                        "--min-distance",
                        "1",
                    ]
                )

            self.assertEqual(exit_code, 0, stderr_buffer.getvalue())

            chapter_files = sorted(output_dir.glob("chapter_*.wav"))
            self.assertGreaterEqual(len(chapter_files), 2)


if __name__ == "__main__":
    unittest.main()
