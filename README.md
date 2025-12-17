# strudel_converter

Convert audio from videos to Strudel code.

## Getting started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```
3. Paste a YouTube/video/audio URL or upload a file to generate Strudel code with tempo, rhythmic grid, and melodic motifs.

The app analyses tempo, onsets, chroma, and pitch using `librosa`, then emits a Strudel snippet you can paste into the [Strudel playground](https://strudel.cc/playground/). The generated script includes:

- `setcpm` tempo metadata and a chord progression derived from the detected key (major or minor).
- A drum grid (kicks plus hat stack), bass line locked to the progression, a lead motif from the detected pitches, and a noise riser.
- Section scaffolding using `arrange(...)` and reusable `let` bindings (drums, bass, pad, lead) combined via `stack(...)`.
