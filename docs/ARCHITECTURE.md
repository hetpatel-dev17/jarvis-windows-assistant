# Architecture

## Command pipeline

1. Browser UI records a short microphone clip, or accepts typed text.
2. The local API authenticates the request and checks its origin.
3. Local Whisper transcribes microphone audio.
4. Common commands route directly to a focused tool. Other requests use OpenJarvis with Ollama.
5. Tools return actual observations. Website sends and uploads require review.
6. One server-side speech worker reads the result through ElevenLabs.

## Main modules

| Module | Responsibility |
| --- | --- |
| `app.py` | Local API, command execution, approval lifecycle, OpenJarvis integration |
| `command_routes.py` | Deterministic spoken/typed command routing |
| `windows_operator.py` | Bounded filename search, fuzzy ranking, numbered results, local opening |
| `file_browser.py` | Restricted attachment selection, separate from general file opening |
| `browser_session.py` | Dedicated normal sign-in profile and owned localhost browser endpoint |
| `site_workflows.py` | Site-tab selection, YouTube search, WhatsApp workflow |
| `media_controls.py` | Actual YouTube player state, volume verification, video history |
| `chatgpt_controls.py` | Visible composer selection, upload, approval, Send, reply readback |
| `single_voice.py` | One playback worker, event deduplication, stop/stale-result handling |
| `desktop_controls.py` | Windows speaker volume and fixed settings shortcuts |
| `key_store.py` | Windows DPAPI key decryption without logging plaintext |

## Concurrency and boundaries

Task execution is serialized. Playwright work uses a dedicated browser thread. Speech uses its own single-worker queue. State locks protect approval and file-result snapshots.

File search uses filename metadata only. Match identifiers expire on the next search. Opening rechecks the chosen path and supported extension. Search cancellation and bounded traversal do not cause an arbitrary file to open.

Browser text is treated as untrusted data. Tools must not use page text to bypass review or change credentials. Browser ownership checks protect the dedicated profile; personal default profiles are not controlled.

## Current engineering limits

There is no always-on wake word, full desktop UI automation, full disk content index, arbitrary command execution, radio toggling, or background morning schedule. Searches do not guarantee exhaustive whole-computer coverage. Website interfaces and anti-automation checks can change. A final product interface is deferred until the pipeline acceptance work is complete.
