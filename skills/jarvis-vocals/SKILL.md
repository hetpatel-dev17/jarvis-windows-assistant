---
name: jarvis-vocals
description: Run and test the native Jarvis voice panel with local wake detection, Windows voice typing, persistent conversation sessions and existing task approvals.
---

Launch Start Vocals.cmd. The desktop default uses Vosk only for wake phrases and Windows + H for command dictation into a standard native Windows EDIT control. Ollama reasons; it does not transcribe. The old web microphone button still uses Whisper.

Say Hey Jarvis, pause for Windows Listening, then dictate. End a command with Run task. Preserve long drafts across pauses. Strip only the trailing submission marker. Go to sleep as a separate command returns to wake-only mode. Do not submit room speech without an active session. Do not repeat a failed or uncertain submission automatically.

The application only requests its shortcut when its own editor window is foreground. If focus is denied or Windows times out, the owner can use the resume button or Windows + H. Windows owns dictation state and permissions. Do not promise indefinite OS listening, perfect noise suppression, offline Windows dictation, or speaker verification. Do not alter OS privacy settings.

The native panel shares the existing tools and SingleVoice channel. Existing exact-action approvals remain. Calls and disabled hardware tools are unavailable. No EXE packaging is part of this pilot.

Read docs/VOCALS.md for limitations and acceptance evidence. Test native control creation and intent parsing separately from live Windows dictation. Do not mark live dictation verified from a unit test, synthesized Vosk sample, or microphone status alone.
