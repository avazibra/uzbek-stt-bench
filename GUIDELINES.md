# Transcription guidelines (v1 draft)

The reference is what was **said**, not what should have been written. Every rule
below exists because at least one engine was scored differently depending on it.

## Format

One speaker turn per line: `[MM:SS] A: text`. `A` is the host who speaks first in
the clip, `B` the other; use `C` only if a third voice appears. The timestamp is
the moment the turn starts, to the nearest second. Short back-channels
("ha", "yo'q", "tushunarli") get their own turn if they interrupt the other speaker.
Lines starting with `#` are comments and are ignored by the scorer.

## Verbatim

- Keep fillers and hesitations: *anaqa, haligi, xullas, endi, ha, hm*.
- Keep repetitions and false starts exactly: *keltirilgan keltirgan*, *asosi, asosi*.
- Keep colloquial morphology as spoken: *ilovani* if that is what was said, not *ilovaning*.
- Do not fix grammar, do not add or remove words for readability.
- Unintelligible: `[?]` for one word, `[??]` for a stretch. Never guess silently.

## Script and spelling

- Uzbek Latin. Apostrophe: the straight `'` (the scorer folds ʻ ’ ‘ into it anyway).
- Russian words and phrases: Latin, as pronounced by the speaker
  (*perevodlar*, *skidka*, *komu ne len*, *kommunalniy*). Never Cyrillic.
- English and brand names: their own spelling (*WeChat, PayPay, SoftBank, Line, Yandex Go*).
  Suffixes attach with an apostrophe: *Payme'ni*, *SoftBank'dan*.
- Local names as commonly written: *Uzmobile, Click, Payme, Kaspi, GAI, texpasport*.
- "Super app": write *super app* (two words). The scorer treats *superapp* and *super-app* as equal.

## Numbers

Numbers as words, as spoken: *yigirma foiz*, *o'ttiz besh mingta*, *yuzta*.
The scorer maps the digit forms engines produce (*20%*, *35000ta*, *100 ta*) onto these.

## Punctuation

Punctuation is ignored by the scorer; use it for readability only. Sentence-final
`?` is welcome because it helps a second annotator.

## Process

1. Open `make edit CLIP=ep40`. Listen to a sentence **before** reading the draft, then correct.
2. Do the whole clip in one pass, then a second pass at 1.25x speed for turn markers and timestamps.
3. When done, remove the `#` header lines, save as `reference/<clip>.txt`, run `make score`.
4. Note anything you were unsure of in `reference/<clip>.notes.md`.

## Known open questions

- Whether to keep laughter and non-speech (`[kulgi]`). Proposal: keep, scorer strips `[...]`.
- Overlapping speech: attribute to the dominant speaker, mark the other's words on their own line.
