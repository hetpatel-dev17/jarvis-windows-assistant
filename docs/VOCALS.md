# Jarvis vocals — testing version

Open **Jarvis Vocals** on the Windows Desktop, or run **Start Vocals.cmd**. A native panel opens without needing the Jarvis webpage. Keep the panel running; minimizing keeps listening active. Closing stops the microphone. It does not start with Windows automatically.

1. Say **Hey Jarvis**.
2. Wait for the greeting.
3. Say **Open YouTube**, **Open Desktop**, or another existing task.
4. Stop speaking. Jarvis detects the pause and sends the task.

Also try **Hey Jarvis, open YouTube** in one sentence. The panel shows recognized words and replies. A greeting leaves a 12-second command window. Recognition is currently English; noise and accent affect accuracy.

The animated ring changes for listening, recording, understanding, working and speaking. The current female Kokoro voice remains in use. No ElevenLabs key is needed. Vosk detects the wake locally; Whisper transcribes locally. Audio buffers stay in memory. The panel does not create a second browser controller or replay speech.

**Pause listening** turns off microphone capture. **Stop task / voice** stops work and spoken output. Listening is suspended during work and speech, so voice interruption is not supported yet. Use the button then. Other speaker audio can trigger a voice assistant; headphones help around videos. This is not speaker identification.

Existing message/upload review is preserved. Review the complete action in the panel. Click Approve/Decline, or wake Jarvis and say approve/decline for the current pending review. No approval applies to future unrelated actions.

This interface exposes existing capabilities. It does not add phone calls, unsupported website operations, Arduino/ESP-IDF execution, or guaranteed uninterrupted browser tasks. No EXE installer was built for this milestone.

## Evidence — 2 November 2026

- 28 unit checks passed, including wake-prefix filtering and microphone-off initialization.
- Native Tk panel opened and closed in a smoke test.
- Authenticated start/status/stop checks reached listening with no microphone error, then off.
- Offline generated female speech, “Hey Jarvis. Open YouTube.”, triggered the actual Vosk model. Actual local Whisper returned “Hey Jarvis, open YouTube.” and wake verification extracted “open YouTube.” No website action was dispatched by this sample test.
- Computer-use visual inspection confirmed the panel and Listening state.
- Owner voice, accent, wake/follow-up timing, false activations and end-to-end spoken tasks remain to be tested. Do not label fully verified until those pass.

Fresh setup installs pinned vosk/sounddevice dependencies and downloads the fixed Apache-2.0 Vosk small English model with SHA-256 validation. Whisper and Kokoro assets stay outside Git. Sources: [Vosk models](https://alphacephei.com/vosk/models), [sounddevice raw streams](https://python-sounddevice.readthedocs.io/en/0.5.3/api/raw-streams.html).
