import os
import numpy as np
import librosa
from pydub import AudioSegment
import sys
import time

# ----------------------
# Dateien
# ----------------------
input_file = "hoerspiel.mp3"
reference_files = ["trennmelodie.mp3", "titelsong.mp3"]  # beide Referenzen
output_dir = "kapitel_ref"

# Parameter
min_distance_between_chapters = 3   # Sekunden Abstand zwischen Kapiteln
hop_length = 512                     # Hop für Sliding Window

# ----------------------
# MP3 -> WAV laden
# ----------------------
audio = AudioSegment.from_mp3(input_file)
audio.export("temp.wav", format="wav")
y, sr = librosa.load("temp.wav", sr=None)  # Original-Sampling-Rate verwenden
duration = librosa.get_duration(y=y, sr=sr)

# ----------------------
# Referenzen laden + dynamische Thresholds berechnen
# ----------------------
reference_chromas = []
reference_thresholds = []

for ref_file in reference_files:
    y_ref, _ = librosa.load(ref_file, sr=sr)  # gleiche Sampling-Rate wie Hauptaudio
    chroma_ref = librosa.feature.chroma_stft(y=y_ref, sr=sr)
    chroma_ref = chroma_ref / (np.linalg.norm(chroma_ref, axis=0, keepdims=True) + 1e-8)
    reference_chromas.append(chroma_ref)

    # Dynamischer Threshold basierend auf Self-Similarity der Referenz
    self_sim = np.mean(np.diag(np.dot(chroma_ref.T, chroma_ref)))
    reference_thresholds.append(self_sim * 0.9)

# ----------------------
# Hörspiel-Chroma
# ----------------------
chroma = librosa.feature.chroma_stft(y=y, sr=sr)
chroma = chroma / (np.linalg.norm(chroma, axis=0, keepdims=True) + 1e-8)
n_frames = chroma.shape[1]

# ----------------------
# Fortschrittsanzeige
# ----------------------
def print_progress_eta(i, total, start_time, bar_length=40):
    fraction = i / total
    arrow = '#' * int(fraction * bar_length)
    spaces = '-' * (bar_length - len(arrow))
    elapsed = time.time() - start_time
    eta = elapsed / fraction - elapsed if fraction > 0 else 0
    sys.stdout.write(f'\rProgress: [{arrow}{spaces}] {int(fraction*100)}% ETA: {int(eta)}s')
    sys.stdout.flush()

# ----------------------
# Kapitelgrenzen erkennen
# ----------------------
chapter_times = []
start_time = time.time()
i = 0

while i < n_frames:
    matched = False
    for chroma_ref, threshold in zip(reference_chromas, reference_thresholds):
        ref_len = chroma_ref.shape[1]
        if i + ref_len > n_frames:
            continue
        window = chroma[:, i:i + ref_len]
        similarity = np.mean(np.sum(window * chroma_ref, axis=0))
        if similarity > threshold:
            time_sec = librosa.frames_to_time(i, sr=sr, hop_length=hop_length)
            if not chapter_times or time_sec - chapter_times[-1] > min_distance_between_chapters:
                chapter_times.append(time_sec)
            # Skip bis Ende der Referenz, damit lange Referenzen nicht mehrfach erkannt werden
            i += ref_len
            matched = True
            break  # keine weiteren Referenzen an diesem Frame prüfen
    if not matched:
        i += 1
    if i % 500 == 0 or i >= n_frames - 1:
        print_progress_eta(i + 1, n_frames, start_time)

print()  # Neue Zeile nach Progress Bar

# ----------------------
# Kapitelgrenzen + Export
# ----------------------
chapter_boundaries = [0.0] + sorted(chapter_times) + [duration]

os.makedirs(output_dir, exist_ok=True)
for idx in range(len(chapter_boundaries) - 1):
    start_ms = int(chapter_boundaries[idx] * 1000)
    end_ms = int(chapter_boundaries[idx + 1] * 1000)
    segment = audio[start_ms:end_ms]
    filename = os.path.join(output_dir, f"kapitel_{idx+1}.mp3")
    segment.export(filename, format="mp3")
    print(f"Kapitel {idx+1} gespeichert: {filename}")
