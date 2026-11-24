---
name: Pull Request
about: Submit a feature, fix, or infrastructure change
title: "[FEAT/FIX/CHORE]: "
---

## Summary

<!-- One-liner: what does this PR do and why? -->

Closes: #ISSUE

## What's Changed

<!-- Bullet list of the main changes. For prompt/docs changes, be explicit. -->

- [ ] Feature / fix implementation
- [ ] Tests added / updated (name the files)
- [ ] Prompt / documentation updates (which files)
- [ ] CI / infra changes (which workflows or configs)

## Checklist

- [ ] `uv run python -m pytest --no-cov` passes (GREEN)
- [ ] `uv run black --check .` passes
- [ ] `uv run flake8 .` passes
- [ ] `uv run mypy --explicit-package-bases --exclude '^tests/' .` passes
- [ ] **Аудит безопасности:** Команда `uv run bandit -r handlers/ db/ utils/ data/ services/` не обнаружила уязвимостей.
- [ ] Docs updated (README, docs/) if behavior changed

## Notes for Reviewers

<!-- Anything reviewers should know: intentional trade-offs, known limitations, follow-ups. -->