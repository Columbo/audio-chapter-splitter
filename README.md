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
- `ffmpeg` installed and available on your system
- Python packages:
  - `numpy`
  - `librosa`
  - `pydub`

## Files Expected By The Script

By default, the script currently expects these files in the project folder:

- `hoerspiel.mp3` for the full story
- `trennmelodie.mp3` for a reference clip
- `titelsong.mp3` for a reference clip

Output is written to:

- `kapitel_ref/`

## Usage

1. Put your full story MP3 into the project folder.
2. Add one or more short reference clips that occur at chapter boundaries.
3. Adjust the filenames in `split_audio_by_reference.py` if your files use different names.
4. Run:

```bash
python split_audio_by_reference.py
```

The script will export separate chapter MP3 files into the output folder.

## Configuration

The script is currently configured directly in the Python file.
You can change:

- input file name
- reference file names
- output folder
- minimum distance between chapter markers
- matching behavior

## Limitations

- The script works best when chapter boundaries contain a clearly repeated audio cue.
- If the reference clip is noisy or inconsistent, detection may be inaccurate.
- The project is currently tailored to a manual workflow rather than a polished command-line tool.
- The included setup batch file may need to be adapted to your local machine.

## Why This Project Exists

This is a practical tool built for a real family use case: turning long children's audio stories into chapter-based tracks that are easier for children to control on a Toniebox.
