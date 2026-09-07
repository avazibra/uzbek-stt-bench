# uzbek-stt-bench

A small, reproducible benchmark of speech-to-text engines on **real conversational
Uzbek**: two podcast hosts, live talk, Uzbek mixed with Russian and English. Vendors
quote numbers on clean read speech (FLEURS); this measures the audio people actually
have.

Status: **v0**. One clip scored against a provisional reference. The listened,
word-by-word reference is in progress; until it lands, treat every number as
indicative, with an error bar of a few points.

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

Audio is not committed; `make clips` fetches it (needs `ffmpeg`).

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

| Engine | WER | Sub | Del | Ins | Words | Proper nouns |
|---|---|---|---|---|---|---|
| gemini-3-flash | 11.4% | 40 | 10 | 11 | 535 | 22/23 |
| muxlisa | 17.8% | 69 | 8 | 18 | 544 | 16/23 |
| gemini-3.5-transcribe-smart | 19.7% | 60 | 40 | 5 | 499 | 21/23 |
| ovoz-ai | 20.4% | 60 | 40 | 9 | 503 | 22/23 |
| gemini-3.5-transcribe | 21.0% | 68 | 32 | 12 | 514 | 19/23 |
| elevenlabs-scribe | 21.5% | 80 | 16 | 19 | 537 | 18/23 |
| uzbekvoice | 23.2% | 89 | 12 | 23 | 545 | 15/23 |
<!-- results:end -->

WER is computed after normalization (`NORMALIZATION_VERSION` in `scripts/score.py`):
lower-case, apostrophe variants folded, punctuation dropped, hyphens split, and a short
public list of orthographic equivalents (`super app` = `superapp`, `20%` = `yigirma foiz`).
Uzbek colloquial vs. standard morphology (`ilovani` vs `ilovaning`) is **not** folded:
the reference is verbatim, and normalizing it is an engine choice we want to see.

"Proper nouns" is the share of reference occurrences of the terms in
`reference/<clip>.terms.txt` that the engine got right. WER hides this; it is where
engines differ most.

## Caveats

- Three clips from one podcast, two male voices, Tashkent Uzbek. Do not generalize to
  read speech, other dialects, or phone audio.
- Engines change weekly. Dates and settings are recorded above; re-run before quoting.
- The provisional reference was adjudicated from engine outputs, not from listening.
  Four engines agreeing on a wrong word can make it into a provisional reference; that
  happened once already ("Qozog'istonda Kaspi").

## Contributing

Add an engine: drop its raw output in `transcripts/<clip>/<engine>.txt`, add a row to
the table above saying how it was run, `make score`. Add a clip: extend `clips.json`,
produce a reference following `GUIDELINES.md`.

Audio © Oddiy Podkast. Transcripts and code: CC BY 4.0 / MIT (to be confirmed).
