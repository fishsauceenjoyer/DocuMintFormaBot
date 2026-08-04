# chore: AI Infrastructure Upgrade, Prompt Hardening & Tech-Debt Audit

## Summary

Upgrades the AI-driven development infrastructure: hardening the prompt suite against logical hallucinations, auditing the codebase for dead code and type/DB-schema discrepancies, adding a meta-orchestrator for the AI model team, and preparing the repo for mutation testing with `mutmut`.

## 🧪 Prompt Optimization & Tech-Debt Audit Budget

### 🛠️ STEP 1 — Audit & Hallucination Fixes
**Dead code removed:**
- `handlers/start.py`: removed unused `import asyncio`.

**Logical discrepancies fixed:**
- `handlers/order.py` (`save_delivery`): delivery field truncation now matches the SQLAlchemy column sizes — `delivery_phone` capped at `String(20)` and `delivery_paczkomat` (address) at `String(100)`, instead of the previous blanket `255`. This prevents `DataError` on PostgreSQL when a user enters a longer phone/address.

**New reference guide:**
- `docs/BUSINESS_CONFIG_GUIDE.md` — the mandatory contract doc for AI models: single source of truth (`data/business_config.py`), DB schema alignment table, currency/language rules, and common pitfalls.

> Note: `data/business_config_original.py` is intentionally kept — it is a documented frozen reference file for restoring original business data, not dead code.

### 📂 STEP 2 — Prompt Engineering
- Added the mandatory **anti-hallucination system rule** to:
  - `prompts/role_developer.md`
  - `prompts/role_qa_automation.md`
  - `prompts/role_pr_reviewer.md`
  *(Rule: read `data/business_config.py` + `docs/BUSINESS_CONFIG_GUIDE.md` before writing any code/test.)*
- Added **`prompts/meta_orchestrator.md`** — the "Chief AI Architect" prompt that coordinates the specialist models (Developer, QA, PR Reviewer, Security, Mutant Killer, Config Validator), enforces architecture boundaries, and rejects hallucinated business values.

### 🧪 STEP 3 — Mutation Testing Preparation
- Added `mutmut==3.7.0` to `[dependency-groups] dev` in `pyproject.toml`.
- Added **`setup.cfg`** with mutmut config: `paths_to_mutate = handlers/`, `tests_dir = tests/`, `runner = pytest`, plus exclusions.
- Verified `uv run mutmut` launches. **Note:** mutmut requires WSL on Windows (per its own message); CI runs on `ubuntu-latest` (Linux) where it executes normally.

### 📄 Docs / Template
- Populated the previously-empty `.github/PULL_REQUEST_TEMPLATE.md` with a full PR template including the Prompt-Optimization & Tech-Debt Audit section.

## Checklist

- [x] `uv run python -m pytest --no-cov` → **408 passed, 2 skipped (GREEN 🟢)**
- [x] `uv run black --check .` → clean (55 files unchanged)
- [x] `uv run flake8 .` → clean
- [x] Docs updated (`docs/BUSINESS_CONFIG_GUIDE.md`, `.github/PULL_REQUEST_TEMPLATE.md`)
- [x] Committed to `chore/ai-infrastructure-upgrade` (`de7135c`)

## Notes for Reviewers

- The only production-code changes are the dead-import removal in `handlers/start.py` and the delivery-truncation alignment in `handlers/order.py`; both are behavior-preserving within normal input ranges and covered by the existing suite.
- `mutmut` is Linux-only for execution; on Windows dev machines use WSL. The CI pipeline targets `ubuntu-latest`, so no workflow change is required.
- The untracked `.github/pull_request_description.md` from a prior task was intentionally excluded from this commit.