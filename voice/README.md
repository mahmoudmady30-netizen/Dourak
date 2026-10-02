# Offline voice pack for the TV queue display (optional)

Many Smart-TV browsers (Samsung Tizen, LG webOS, most Android TV WebViews)
have **no speech engine at all** — the display shows "unsupported". The
TV audio engine can then speak using short recorded clips instead, fully
offline, through Web Audio (supported on virtually every TV).

Record these clips (any phone voice recorder, MP3 or WAV, trimmed tightly):

| file         | Arabic (voice/ar/)        | English (voice/en/)   |
|--------------|---------------------------|-----------------------|
| prefix.mp3   | "الرقم"                   | "Number"              |
| a.mp3        | "إيه" (letter A, optional)| "A" (optional)        |
| 0.mp3 … 9.mp3| صفر … تسعة                | zero … nine           |
| suffix.mp3   | "تفضل إلى الخدمة"          | "please proceed"      |
| recall.mp3   | "نداء مرة أخرى" (optional) | "calling again" (opt.)|

Then create `voice/ar/manifest.json` (same shape for `en`):

```json
{ "files": { "prefix": "prefix.mp3", "a": "a.mp3", "suffix": "suffix.mp3",
  "recall": "recall.mp3", "0": "0.mp3", "1": "1.mp3", "2": "2.mp3",
  "3": "3.mp3", "4": "4.mp3", "5": "5.mp3", "6": "6.mp3", "7": "7.mp3",
  "8": "8.mp3", "9": "9.mp3" } }
```

No manifest = pack disabled (the engine silently skips this layer).
