# strudel_converter

Convert audio from videos to Strudel code.

## Getting started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   - Stem separation with Spleeter requires **Python 3.8–3.10**. Install the optional stack via:
     ```bash
     pip install -r requirements-spleeter.txt
     ```
     It pins TensorFlow 2.10.1 and protobuf 3.20.3. On Python 3.11+ or without these pins, Spleeter will fail to import and the
     app will fall back to feature extraction without stems.
2. Run the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```
3. Paste a YouTube/video/audio URL or upload a file to generate Strudel code with tempo, rhythmic grid, and melodic motifs.

The app analyses tempo, onsets, chroma, and pitch using `librosa`, and also separates stems with `spleeter` (vocals, drums, bass, other) to better map kicks/snares, bass movement, and melodic hooks. It emits a Strudel snippet you can paste into the [Strudel playground](https://strudel.cc/playground/). The generated script includes:

- `setcpm` tempo metadata and a chord progression derived from the detected key (major or minor).
- A drum grid using `tr808_bd`, `tr808_sd`, and hats, a bass line locked to the progression (preferring bass stem notes), a lead motif (preferring vocal stem pitches), and a noise riser.
- Section scaffolding using `arrange(...)` and reusable `let` bindings (drums, bass, pad, lead) combined via `stack(...)`.

> **Note:** Spleeter downloads model data on first run; ensure `ffmpeg` is installed and that you have enough disk and memory headroom for stem separation.
