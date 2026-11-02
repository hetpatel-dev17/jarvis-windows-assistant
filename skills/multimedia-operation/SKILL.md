---
name: multimedia-operation
description: Use the existing YouTube, speaker-volume, and local-media opening tools. Use for playback, next/previous, seeking, mute, volume, and a selected local media file.
---

# Multimedia operation

Use `youtube_control` for YouTube player state and history. A search followed by “play the first one” refers to its current results. Confirm playback state rather than treating an open homepage as playback.

Plain volume commands refer to YouTube. Explicit computer/system/Windows volume uses `desktop_control`. Local media opening uses `windows_operator` and the chosen result; a Windows launch request is not proof that the destination app played the file.

The existing single speech channel prevents duplicate Jarvis replies. Keep that channel when changing voice settings. Broader multimedia app control remains unverified.
