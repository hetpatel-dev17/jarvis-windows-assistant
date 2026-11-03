# Jarvis vocals â€” Windows voice typing pilot

Updated 3 November 2026. The default desktop command path now uses Windows + H voice typing. Vosk is used only for wake detection. Ollama remains the reasoning engine. Whisper is still available to the older web recording button, but it is not called for desktop wake or Windows-dictated commands.

## Use

Open Jarvis Vocals. Enable listening if paused. Say **Hey Jarvis**, **Hello Jarvis**, or **Open Jarvis**, then pause. Jarvis focuses its native Windows text box and requests Windows voice typing. Wait for the Windows **Listening** indicator. Dictate a command and end with **Run task**. For example: **Open YouTube. Run task.** The suffix is removed before submission. Pauses alone never submit drafts. A one-second stable-text check lets Windows finish punctuation before the marker is consumed.

The conversation session remains awake between tasks. The panel requests dictation again after work and spoken output finish. Say **Go to sleep** as a separate utterance to return to wake-only listening. There is no 12-second follow-up timeout in this mode. Use **Windows typing / resume** if Windows has paused dictation. Windows itself can time out or reject background focus; this software cannot guarantee a permanent Windows microphone session.

Run task and Go to sleep are reserved control phrases. Do not use those phrases as literal command endings in this pilot. A pending message/upload approval can receive **Approve. Run task.** or **Decline. Run task.** Existing exact-action review is preserved. The Stop task / voice button remains available during work; barge-in is not supported.

The editing surface is now the standard native Windows EDIT control, hosted inside the panel. It is no longer a Tk-only entry. The application checks that its own window is foreground before issuing its voice-typing shortcut. If Windows refuses foreground activation, click the Jarvis text box and use Windows + H. It will not issue the shortcut into another app. No global keyboard hook, browser controller, or clipboard reader was added.

Windows dictation requires internet and uses Microsoft speech processing. Windows manages its microphone, language, punctuation, noise suppression and permissions. Jarvis does not change Windows privacy settings. If Windows asks for setup or permission, handle that directly. Do not claim perfect echo suppression or speaker identification.

On Go to sleep the editor is locked and dictation dismissal is attempted. Confirm the Windows indicator stopped; say Windows' **Stop listening** if it remains active. Closing Jarvis stops its Vosk listener and attempts to dismiss dictation, but Jarvis does not own the Windows service. Pause listening disables Jarvis wake capture; use Windows' own stop control to stop Windows capture too.

## Verification

- 30 unit checks passed, including explicit end-marker parsing, draft preservation rules, separate sleep intent, wake-prefix checks and awake/sleep session state.
- Native Windows editor and panel smoke test opened and closed without an exception.
- Python syntax passed.
- Earlier 2 November tests proved local Vosk detection on generated speech and actual microphone startup. Those do not prove the new Windows dictation handoff.
- Windows + H live transcription, automatic reopening after browser work, echo handling and the owner's voice remain pending. The agent did not trigger the Windows-key shortcut during verification. This is a pilot, not a verified continuous Windows dictation implementation.

[Microsoft voice typing guide](https://support.microsoft.com/en-us/accessibility/windows/use-voice-typing-to-talk-instead-of-type-on-your-pc) documents the focused-text-box requirement, internet use and Windows controls. The existing browser, downloads and message capabilities are unchanged. Calls remain unavailable.
