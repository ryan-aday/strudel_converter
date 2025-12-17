import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

import librosa
import numpy as np
import soundfile as sf
import yt_dlp
from spleeter.separator import Separator

logger = logging.getLogger(__name__)


SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a", ".mp4", ".mov"}


def is_supported_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def download_audio(source_url: str) -> Path:
    """Download audio from a URL (YouTube or direct) into a temporary file."""
    temp_dir = Path(tempfile.mkdtemp(prefix="strudel_audio_"))
    output_template = str(temp_dir / "audio.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        logger.info("Downloading audio from %s", source_url)
        ydl.download([source_url])

    downloaded = next(temp_dir.glob("audio.*"), None)
    if downloaded is None:
        raise FileNotFoundError("Failed to download audio file")

    return downloaded


def save_upload_to_temp(upload_bytes: bytes, filename: str) -> Path:
    """Persist an uploaded file to a temporary path for analysis."""
    temp_dir = Path(tempfile.mkdtemp(prefix="strudel_upload_"))
    target = temp_dir / Path(filename).name
    with open(target, "wb") as f:
        f.write(upload_bytes)
    return target


def load_audio(audio_path: Path, target_sr: int = 44100) -> Tuple[np.ndarray, int]:
    """Load an audio file with librosa, resampling as needed."""
    y, sr = librosa.load(audio_path, sr=target_sr, mono=True)
    return y, sr


def extract_features(y: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
    """Compute useful features for rhythm and pitch estimation."""
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)

    onset_times = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, units="time", backtrack=True
    )

    pitches = librosa.yin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
        frame_length=2048,
    )

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

    return {
        "onset_env": onset_env,
        "tempo": np.array([tempo]),
        "beat_frames": beat_frames,
        "onset_times": onset_times,
        "pitches": pitches,
        "chroma": chroma,
    }


def separate_stems(audio_path: Path, stems: str = "spleeter:4stems") -> Dict[str, Tuple[np.ndarray, int]]:
    """Use Spleeter to separate stems and return loaded arrays keyed by instrument."""
    temp_dir = Path(tempfile.mkdtemp(prefix="strudel_stems_"))
    separator = Separator(stems)

    separator.separate_to_file(
        str(audio_path),
        str(temp_dir),
        filename_format="{filename}/{instrument}.wav",
    )

    base_folder = temp_dir / Path(audio_path).stem
    stems_loaded: Dict[str, Tuple[np.ndarray, int]] = {}
    for stem_file in base_folder.glob("*.wav"):
        data, stem_sr = sf.read(stem_file)
        if data.ndim > 1:
            data = np.mean(data, axis=1)
        stems_loaded[stem_file.stem] = (data.astype(np.float32), stem_sr)

    return stems_loaded


def dominant_key(chroma: np.ndarray) -> str:
    """Estimate a dominant pitch class from chroma energy."""
    pitch_classes = [
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    ]
    if chroma.size == 0:
        return "C"
    energy = chroma.mean(axis=1)
    idx = int(np.argmax(energy))
    return pitch_classes[idx]


def note_sequence_from_pitch_track(pitches: np.ndarray, sr: int, onset_times: np.ndarray) -> List[str]:
    """Sample the pitch contour at onset positions and map to note names."""
    if len(pitches) == 0 or len(onset_times) == 0:
        return []

    times = librosa.frames_to_time(np.arange(len(pitches)), sr=sr)
    notes: List[str] = []

    for onset in onset_times:
        idx = np.searchsorted(times, onset)
        if idx >= len(pitches):
            idx = -1
        pitch_hz = pitches[idx]
        if np.isnan(pitch_hz) or pitch_hz <= 0:
            continue
        notes.append(librosa.hz_to_note(pitch_hz))

    return notes


def grid_rhythm(onset_times: np.ndarray, tempo: float, grid: int = 16) -> List[str]:
    """Map onset times onto a step grid to build a percussive pattern."""
    if tempo <= 0 or len(onset_times) == 0:
        return []

    seconds_per_beat = 60.0 / tempo
    pattern = ["~"] * grid

    for onset in onset_times:
        beat_position = onset / seconds_per_beat
        step = int(np.round((beat_position % 4) / 4 * grid)) % grid
        pattern[step] = "bd"

    return pattern


def export_audio_clip(y: np.ndarray, sr: int, duration: float = 12.0) -> Path:
    """Save a short preview clip for reference."""
    samples = int(duration * sr)
    clip = y[:samples]
    temp_dir = Path(tempfile.mkdtemp(prefix="strudel_preview_"))
    clip_path = temp_dir / "preview.wav"
    sf.write(clip_path, clip, sr)
    return clip_path
