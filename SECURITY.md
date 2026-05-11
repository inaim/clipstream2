# Security Policy

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report security issues by emailing **issam.naim@gmail.com** with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix (optional)

We will acknowledge receipt within 48 hours and aim to release a fix within 14 days for critical issues.

## Scope

In scope:
- Authentication and authorisation bypasses
- SQL/NoSQL injection in SurrealDB queries
- JWT vulnerabilities
- IPFS content integrity issues
- Smart contract vulnerabilities in `$WATCH` token

Out of scope:
- Rate limiting bypasses (known limitation, tracked separately)
- Issues in third-party dependencies not yet patched upstream
- Social engineering attacks

## Responsible Disclosure

We ask for a 90-day responsible disclosure window before public disclosure, to allow us to release a fix.
