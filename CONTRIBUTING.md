# Contributing to ClipStream

Thank you for your interest. ClipStream is building the open-source alternative to TikTok — with creator-owned economics and the same recommendation engine. Every contribution matters.

## Before You Start

- Read the [README](README.md) and understand the project goals
- Check [open issues](https://github.com/inaim/clipstream2/issues) — your idea may already be tracked
- For significant changes, open an issue first to align before writing code

## Development Setup

```bash
git clone https://github.com/inaim/clipstream2
cd clipstream2
bash START_TIKTOK_PLATFORM.sh
```

See the README Quick Start for full details.

## Where to Contribute

| Area | Docs | Skills |
|---|---|---|
| Monolith Phase 2 (online retraining) | [MONOLITH_ANALYSIS.md](docs/architecture/MONOLITH_ANALYSIS.md) | Python, ML, PyTorch |
| Filecoin archival | [docs/architecture/](docs/architecture/) | Web3, IPFS, Solidity |
| Mobile app | [docs/api/ENDPOINTS.md](docs/api/ENDPOINTS.md) | React Native |
| Live streaming | [docs/architecture/SCALING.md](docs/architecture/SCALING.md) | WebRTC, media servers |
| DAO governance | [docs/architecture/](docs/architecture/) | Solidity, tokenomics |
| Frontend features | [frontend/src/components/](frontend/src/components/) | React, TypeScript |

## Workflow

1. **Fork** the repository and create a branch from `main`
2. **Name your branch** descriptively: `feat/online-training`, `fix/embedding-ttl`, `docs/monolith-phase2`
3. **Write your code** — keep changes focused; one concern per PR
4. **Test** your changes locally before submitting
5. **Open a PR** against `main` — fill in the template completely

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add online model retraining every 60 seconds
fix: prevent embedding table memory leak on cleanup
docs: document UCB exploration formula
refactor: extract scoring into separate module
test: add integration test for swipe → SSE pipeline
chore: upgrade FastAPI to 0.110
```

## Code Standards

**Python (backend)**
```bash
black backend/
flake8 backend/
mypy backend/
```

**TypeScript (frontend)**
```bash
npm run lint
npm run typecheck
```

## Pull Request Checklist

- [ ] Tests pass locally (`pytest` / `npm run test`)
- [ ] Linting passes
- [ ] PR description explains *why*, not just *what*
- [ ] Docs updated if behaviour changed

## Reporting Bugs

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md). Include reproduction steps — we cannot fix what we cannot reproduce.

## Security Issues

Do **not** open a public issue for security vulnerabilities. See [SECURITY.md](SECURITY.md).

## Questions

Open a [Discussion](https://github.com/inaim/clipstream2/discussions) — not an issue — for questions and ideas.
