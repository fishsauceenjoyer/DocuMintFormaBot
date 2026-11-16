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

## 🧪 Budget of Prompt Optimization & Tech-Debt Audit

> For `chore/ai-infrastructure-upgrade`-style PRs, fill this section.

### Prompt Engineering
- **Anti-hallucination rule added to:** `prompts/role_developer.md`, `prompts/role_qa_automation.md`, `prompts/role_pr_reviewer.md`
- **New orchestrator prompt:** `prompts/meta_orchestrator.md`
- **New reference guide:** `docs/BUSINESS_CONFIG_GUIDE.md`

### Tech-Debt / Dead-Code Audit
- Files audited: `handlers/`, `db/`, `utils/`
- Dead code removed: `<list, e.g. unused import asyncio in handlers/start.py>`
- Logical discrepancies fixed: `<list, e.g. delivery field truncation aligned to DB column sizes>`

### Mutation Testing (mutmut)
- `mutmut` added to `[dependency-groups] dev` in `pyproject.toml`
- Config: `setup.cfg` (`paths_to_mutate`, `tests_dir`, `runner`)
- Status: `uv run mutmut` verified (Windows requires WSL; CI runs on Linux)

## Checklist

- [ ] `uv run python -m pytest --no-cov` passes (GREEN)
- [ ] `uv run black --check .` passes
- [ ] `uv run flake8 .` passes
- [ ] `uv run mypy --explicit-package-bases --exclude '^tests/' .` passes
- [ ] **Аудит безопасности:** Команда `uv run bandit -r handlers/ db/ utils/ data/ services/` не обнаружила уязвимостей.
- [ ] Docs updated (README, docs/) if behavior changed

## Notes for Reviewers

<!-- Anything reviewers should know: intentional trade-offs, known limitations, follow-ups. -->