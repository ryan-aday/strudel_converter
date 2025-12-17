import logging
from pathlib import Path
import streamlit as st

from strudel_converter.audio_tools import (
    download_audio,
    extract_features,
    is_supported_file,
    load_audio,
    note_sequence_from_pitch_track,
    separate_stems,
    SUPPORTED_EXTENSIONS,
    save_upload_to_temp,
)
from strudel_converter.strudel_generator import build_strudel_result

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Strudel Converter", layout="wide")
st.title("Strudel Converter")
st.caption("Turn videos and audio into playable Strudel code")


def _analyze(audio_path: Path):
    with st.spinner("Analyzing audio..."):
        y, sr = load_audio(audio_path)
        features = extract_features(y, sr)
        stem_payload = {}

        try:
            stems = separate_stems(audio_path)
            for name, (stem_audio, stem_sr) in stems.items():
                stem_features = extract_features(stem_audio, stem_sr)
                stem_features["notes"] = note_sequence_from_pitch_track(
                    stem_features["pitches"],
                    sr=stem_sr,
                    onset_times=stem_features["onset_times"],
                )
                stem_payload[name] = stem_features
        except Exception as exc:  # pragma: no cover - optional path
            logger.warning("Stem separation failed: %s", exc)

        result = build_strudel_result(
            tempo=float(features["tempo"][0]),
            chroma=features["chroma"],
            pitches=features["pitches"],
            sr=sr,
            onset_times=features["onset_times"],
            audio=y,
            stems=stem_payload,
        )
    return result


def _download_section():
    st.subheader("Link a video or audio file")
    url = st.text_input("YouTube, MP4, or direct audio URL")
    if st.button("Download & Convert", type="primary"):
        if not url:
            st.warning("Please provide a URL to download audio from.")
            return
        try:
            audio_file = download_audio(url)
            result = _analyze(audio_file)
            st.success("Conversion complete!")
            st.code(result.to_code(), language="haskell")
            if result.preview_path:
                st.audio(str(result.preview_path))
        except Exception as exc:  # pragma: no cover - streamlit surface only
            logger.exception("Error during download")
            st.error(f"Failed to process audio: {exc}")


def _upload_section():
    st.subheader("Upload audio or video")
    uploaded = st.file_uploader(
        "Upload a file (wav, mp3, ogg, flac, aac, m4a, mp4, mov)",
        type=[ext.strip(".") for ext in sorted(list(SUPPORTED_EXTENSIONS))],
    )
    if uploaded is None:
        return

    if not is_supported_file(uploaded.name):
        st.error("Unsupported file type")
        return

    temp_path = save_upload_to_temp(uploaded.getbuffer(), uploaded.name)
    if st.button("Convert upload", type="primary"):
        try:
            result = _analyze(temp_path)
            st.success("Conversion complete!")
            st.code(result.to_code(), language="haskell")
            if result.preview_path:
                st.audio(str(result.preview_path))
        except Exception as exc:  # pragma: no cover - streamlit surface only
            logger.exception("Error during upload processing")
            st.error(f"Failed to process audio: {exc}")


with st.sidebar:
    st.markdown(
        """
        ### How it works
        1. Paste a YouTube or video/audio URL **or** upload a file.
        2. The app downloads the audio, extracts rhythm & pitch cues (tempo, onsets, chroma, YIN pitch).
        3. It generates Strudel code with stacked note and percussive patterns, tempo metadata, and a preview clip.

        The output favors musical structure by snapping transients to a step grid and prioritizing repeated notes for motifs.
        """
    )
    st.markdown(
        """**Tip:** You can paste the generated snippet into the [Strudel playground](https://strudel.cc/playground/) and swap instruments or effects as needed."""
    )

_upload_section()
st.divider()
_download_section()
