# Verification matrix

Recorded during development on Windows, 1 November 2026. Live checks are observations on one computer, not a universal reliability guarantee. Automated fixture checks are separately identified.

| Pipeline | Evidence | Remaining acceptance work |
| --- | --- | --- |
| Windows file operator | Automated tests for fragments, typos, ambiguity, chosen-match opening, stale/deleted results, cancellation, partial search, and blocked file types | Large drives, offline files, more accessibility testing |
| Voice command wiring | Browser UI checks for recording/transcription dispatch and explicit review mode | More accents, noisy rooms, long transcripts |
| Single voice channel | Worker tests and multiple-tab UI checks; real ElevenLabs synthesis tested | Audio-device changes and suspend/resume |
| YouTube playback | Live search/play, next, previous, pause, volume, mute/unmute, zero-volume recovery; independent browser fixtures | Playlists, live streams, region/ad variations |
| ChatGPT | Live new chat, actual answer readback, history search, approved PDF upload plus final Send and receipt confirmation | More attachment types and site layout changes |
| WhatsApp | One approved outgoing test message observed; fixture checks for exact chat/draft and retry handling | More contact ambiguities; delivery/read receipts are not verified |
| Windows sound/settings | Real volume adjustment restored; fixed settings links tested | More audio devices; settings switches remain manual |
| Gmail / Calendar | User completed browser sign-in | Authenticated reading and summarization acceptance tests |
| Fresh Windows setup | Dependency script, checksum pin, Python/PowerShell syntax and CI checks | Full clean-machine installation |

Do not replace a missing check with a success claim. Record the trigger, observed result, and remaining limitation when adding evidence.
