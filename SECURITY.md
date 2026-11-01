# Security reporting

Do not post secrets or private account data in a public issue. Use GitHub's private vulnerability reporting when enabled on this repository. If that option is unavailable, open a public issue containing only a request for a private reporting channel.

This prototype controls signed-in websites and can open local documents. It is designed for a trusted Windows user on a personal machine. Do not expose its localhost API or browser-control endpoint to a network.

Important boundaries include local API authentication, origin checks, a dedicated browser profile, explicit submission review, filesystem revalidation, supported local file types, and no automatic retry after an uncertain send.

No security audit or production certification is claimed.
