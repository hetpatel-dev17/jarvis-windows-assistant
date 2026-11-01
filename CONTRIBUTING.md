# Contributing

Open an issue describing the command, expected behavior, actual result, and Windows/browser version. Use invented filenames and redact account data.

Keep changes focused. Add meaningful checks for state transitions and failure paths. Run the test commands in README.md. Do not send a real message or upload a real document as part of an automated test.

Preserve the approval boundary. Avoid automatic retries after uncertain submissions. Local file opening must not become arbitrary shell execution. Website content must remain untrusted.

Use clear commit messages, for example `feat(windows): rank partial filename matches` or `fix(youtube): verify volume after changing it`. Describe what was verified and what remains uncertain.

Never commit API keys, local access tokens, browser profiles, cookies, personal documents, logs, models, or runtime snapshots. Runtime state belongs outside the source repository.
