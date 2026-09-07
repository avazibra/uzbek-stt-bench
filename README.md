# uzbek-stt-bench

A small, reproducible benchmark of speech-to-text engines on **real conversational
Uzbek**: two podcast hosts, live talk, Uzbek mixed with Russian and English. Vendors
quote numbers on clean read speech (FLEURS); this measures the audio people actually
have.

Status: **v0.1**. One clip (ep40) scored against a reference transcribed word by word
from the audio by a native speaker. Two more clips (ep1, ep77) have audio but no
reference yet. One annotator, one pass: expect an error bar of a couple of points
until a second pass or annotator exists.

## What is in here

| Path | What |
|---|---|
| `clips.json` | The three 5-minute clips: episode, public audio URL, start offset, why chosen |
| `scripts/fetch_clips.py` | Downloads the episodes from the podcast's public RSS audio and cuts the clips (no re-encoding) |
| `transcripts/<clip>/<engine>.txt` | Raw engine outputs, unedited |
| `reference/<clip>.txt` | The reference transcript, one speaker turn per line |
| `reference/<clip>.terms.txt` | Proper nouns and code-switched terms scored separately |
| `reference/<clip>.draft.txt` | Starting point for the human pass |
| `scripts/score.py` | WER + proper-noun accuracy; regenerates `results/` and the table below |
| `tools/editor.html` | Audio + text side by side for producing the reference |
| `GUIDELINES.md` | Transcription rules. Every scoring dispute is settled there |

The three clips are committed (about 14 MB). `make clips` re-cuts them from the public episode audio if you want to verify them (needs `ffmpeg`).

## Run

```
make clips     # fetch audio
make score     # score, write results/*.md, update this README
make edit      # reference editor at http://localhost:8765/tools/editor.html?clip=ep40
```

## Engines (ep40, 2026-09-07)

| Engine | How it was run |
|---|---|
| gemini-3-flash | AI Studio, temperature 0, grounding off, prompt: "Transcribe this Uzbek podcast audio verbatim in Uzbek Latin script. Keep every word, including fillers; do not summarize, translate, or normalize. Output only the transcript." |
| gemini-3.5-transcribe | AI Studio, defaults (speaker labels + word timestamps on, language Detect) |
| gemini-3.5-transcribe-smart | Same, "Smart transcription" on (disables speakers/timestamps) |
| elevenlabs-scribe | API, `scribe_v1`, language `uzb` |
| muxlisa | muxlisa.uz web upload, `.docx` export |
| uzbekvoice | uzbekvoice.ai web upload, `.docx` export (timestamps stripped) |
| ovoz-ai | Ovoz AI Telegram bot |

## Results

<!-- results:start -->
### ep40

| Engine | WER | WER A | WER B | WER C | Sub | Del | Ins | Words | Proper nouns | Speaker acc | Spk/turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemini-3-flash | 15.3% | 27.0% | 13.2% | 14.6% | 51 | 27 | 7 | 535 | 20/21 | — | — |
| muxlisa | 22.2% | 22.2% | 25.2% | 18.6% | 90 | 22 | 11 | 544 | 15/21 | — | — |
| ovoz-ai | 23.4% | 42.9% | 20.3% | 21.7% | 68 | 57 | 5 | 503 | 21/21 | — | — |
| gemini-3.5-transcribe-smart | 24.5% | 46.0% | 22.9% | 20.4% | 74 | 59 | 3 | 499 | 19/21 | — | — |
| elevenlabs-scribe | 24.9% | 42.9% | 23.7% | 21.2% | 100 | 28 | 10 | 537 | 17/21 | 83% | 2/13 |
| gemini-3.5-transcribe | 25.8% | 34.9% | 25.9% | 23.0% | 92 | 46 | 5 | 514 | 18/21 | 57% | 3/4 |
| uzbekvoice | 28.1% | 42.9% | 25.2% | 27.4% | 114 | 26 | 16 | 545 | 13/21 | — | — |

Speaker acc: word-weighted share of reference turns whose start lies in a hypothesis turn of the matching speaker (hypothesis labels mapped 1:1 to hosts by best overlap). Spk/turns: distinct speakers and turns the engine produced; the reference has 3/21.
<!-- results:end -->

WER is computed after normalization (`NORMALIZATION_VERSION` in `scripts/score.py`):
lower-case, apostrophe variants folded, punctuation dropped, hyphens split, and a short
public list of orthographic equivalents (`super app` = `superapp`, `20%` = `yigirma foiz`).
Uzbek colloquial vs. standard morphology (`ilovani` vs `ilovaning`) is **not** folded:
the reference is verbatim, and normalizing it is an engine choice we want to see.

"Proper nouns" is the share of reference occurrences of the terms in
`reference/<clip>.terms.txt` that the engine got right. WER hides this; it is where
engines differ most. "WER A/B/C" attributes each error to the host whose words it
falls on; "Speaker acc" scores diarization for engines that label speakers (see
`results/<clip>.md` for the definition).

## Caveats

- Three clips from one podcast, three male voices, Tashkent Uzbek. Do not generalize to
  read speech, other dialects, or phone audio.
- Engines change weekly. Dates and settings are recorded above; re-run before quoting.
- An earlier provisional reference was adjudicated from engine outputs instead of
  listening. It was wrong in ways four engines agreed on ("Qozog'istonda Kaspi" was
  missing) and it merged three hosts into one. Never score against engine consensus.
- ep40 has **three** voices, not two: a third host joins at 02:30. Diarization is scored
  against that.

## Contributing

Add an engine: drop its raw output in `transcripts/<clip>/<engine>.txt`, add a row to
the table above saying how it was run, `make score`. Add a clip: extend `clips.json`,
produce a reference following `GUIDELINES.md`.

Audio, references and engine outputs: CC BY 4.0 (the podcast is the author's own). Code: MIT. See `LICENSE`.
