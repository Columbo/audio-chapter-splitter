# audio-chapter-splitter

A small Python tool to split long MP3 child stories into separate chapter files automatically.

I created this project to prepare audio files for a Toniebox. Many children's stories are distributed as one long MP3, which makes it harder for a child to jump back and forth between story sections. By splitting the audio into separate chapter tracks, the child can navigate more easily.

## What Problem This Solves

If a children's story is stored as a single long MP3, playback devices like the Toniebox treat it as one continuous file. That means:

- no natural chapter navigation
- harder to repeat a favorite part
- harder to skip to the next section

This script helps by finding recurring audio markers, for example a title song or short transition melody, and using them as automatic split points.

## How It Works

My workflow starts outside Python:

1. I record or prepare the full story as one long audio file in Audacity.
2. In Audacity, I listen for short sections that repeat throughout the story, for example the title melody or short transition melodies between chapters.
3. I export those short repeated sections as separate MP3 files.
4. These short files become the reference clips, or "divider melodies", that the script searches for.

The script compares the full story audio against one or more of these short reference audio files.
When it detects a strong match, it treats that point as a chapter boundary.
It then exports each chapter as its own MP3 file.

This is useful when the story contains repeated audio cues between chapters.

## Typical Use Case

Example:

- record a full children's story in Audacity and export it as one long `hoerspiel.mp3`
- cut out a short `trennmelodie.mp3` clip that appears between chapters
- optionally cut out a `titelsong.mp3` clip if the title melody also repeats at useful positions

The script scans the full story file, detects these repeated divider melodies, and writes chapter files into an output folder.

## Requirements

- Python 3
- `ffmpeg` installed and available on your system `PATH`
- Python dependencies from `requirements.txt`

## Installation

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

You also need `ffmpeg` installed separately on your system, because it is not a Python package and is required by `pydub` for MP3 handling.

To install `ffmpeg`:

- Official download page: <https://ffmpeg.org/download.html>

- Windows:
  - the official FFmpeg project links to Windows builds here: <https://www.gyan.dev/ffmpeg/builds/>
  - extract it to a local folder
  - add the `bin` folder containing `ffmpeg.exe` to your system `PATH`
  - example: if you extracted FFmpeg to `C:\tools\ffmpeg`, add `C:\tools\ffmpeg\bin` to your `PATH`
- macOS:
  - install it with Homebrew using `brew install ffmpeg`
- Linux:
  - install it with your package manager, for example `sudo apt install ffmpeg`

To verify the installation, run:

```bash
ffmpeg -version
```

If that command prints version information, `ffmpeg` is installed correctly and available on your `PATH`.

On Windows, extending the `PATH` variable means adding the folder that contains `ffmpeg.exe` to the list of folders that Windows searches when you run commands in a terminal.

Example:

- if `ffmpeg.exe` is located in `C:\tools\ffmpeg\bin`
- add `C:\tools\ffmpeg\bin` to the `PATH` variable
- then you can run `ffmpeg -version` from any terminal window without typing the full file path

Typical Windows steps:

1. Open the Start menu and search for `Environment Variables`.
2. Open `Edit the system environment variables`.
3. Click `Environment Variables...`.
4. Under `User variables` or `System variables`, select `Path`.
5. Click `Edit`.
6. Click `New`.
7. Paste the full path to the FFmpeg `bin` folder, for example `C:\tools\ffmpeg\bin`.
8. Confirm with `OK` in all open dialogs.
9. Open a new terminal window and run `ffmpeg -version`.

On Linux, extending the `PATH` variable means adding the folder that contains the `ffmpeg` executable to the list of folders your shell searches when you run commands.

In many Linux installations, `ffmpeg` is installed by the package manager into a standard location and no manual `PATH` change is needed.
If you install a custom build in a separate folder, you may need to add that folder yourself.

Example:

- if the `ffmpeg` executable is located in `/opt/ffmpeg/bin`
- add `/opt/ffmpeg/bin` to your `PATH`
- then you can run `ffmpeg -version` from any terminal window without typing the full file path

Temporary change for the current terminal session:

```bash
export PATH="/opt/ffmpeg/bin:$PATH"
```

Persistent change for future terminal sessions:

1. Open your shell configuration file, for example `~/.bashrc` or `~/.zshrc`.
2. Add this line:

```bash
export PATH="/opt/ffmpeg/bin:$PATH"
```

3. Save the file.
4. Reload the configuration with `source ~/.bashrc` or open a new terminal.
5. Run `ffmpeg -version` to verify it works.

If you want a quick setup helper instead of installing manually:

- Windows: run `setup_hoerspiel_env.bat`
- Linux or macOS: run `sh setup_hoerspiel_env.sh`

Both scripts create a virtual environment in `venv/` and install the Python dependencies from `requirements.txt`.

## Files Expected By The Script

The script now accepts file paths through CLI arguments, so your audio files do not need fixed names.
You need:

- one main audio file, for example `hoerspiel.mp3`
- one or more reference clips, for example `trennmelodie.mp3` and `titelsong.mp3`

By default, output is written to:

- `kapitel_ref/`

## Usage

Run the script with your input file and one or more reference clips:

```bash
python split_audio_by_reference.py \
  --input hoerspiel.mp3 \
  --reference trennmelodie.mp3 \
  --reference titelsong.mp3 \
  --output kapitel_ref
```

The script will export separate chapter MP3 files into the output folder.

You can inspect all available options with:

```bash
python split_audio_by_reference.py --help
```

## Configuration

Important CLI options:

- `--input` for the main audio file
- `--reference` for each divider melody
- `--output` for the export folder
- `--min-distance` for the minimum gap between detected chapter markers
- `--hop-length` for chroma analysis tuning
- `--threshold-scale` for detection sensitivity
- `--keep-temp` to keep the temporary WAV file for debugging

## Limitations

- The script works best when chapter boundaries contain a clearly repeated audio cue.
- If the reference clip is noisy or inconsistent, detection may be inaccurate.
- The current implementation exports chapter files as `kapitel_1.mp3`, `kapitel_2.mp3`, and so on.
- If no divider melody is detected, the script exports the full audio as a single chapter file.

## Legal Note

This tool is intended for processing audio that you created yourself or are otherwise authorized to use.
You are responsible for ensuring that your use of any source audio complies with applicable copyright, licensing, and platform rules.
This project is not affiliated with or endorsed by tonies.

## Why This Project Exists

This is a practical tool built for a real family use case: turning long children's audio stories into chapter-based tracks that are easier for children to control on a Toniebox.
