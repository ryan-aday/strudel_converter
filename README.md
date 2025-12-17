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

The app analyses tempo, onsets, chroma, and pitch using `librosa`, then emits a Strudel snippet you can paste into the [Strudel playground](https://strudel.cc/playground/).
