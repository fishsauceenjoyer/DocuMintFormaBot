# Screenshots

Below are placeholder screenshots showing the main user flows of the bot.
Replace these with real screenshots when you have a running bot instance.

## 1. Main Menu (`/start`)

![Main menu](screenshots/main_menu.png)
*Main menu with available document types.*

## 2. Document Selection & Quantity

![Document choice](screenshots/document_choice.png)
*User selects a document type, sees the price, and chooses quantity.*

## 3. Field Filling

![Field filling](screenshots/field_filling.png)
*User fills in document fields one by one with validation hints.*

## 4. Payment & Confirmation

![Payment](screenshots/payment.png)
*Payment method selection and order confirmation.*

---

> **Note:** Generate real screenshots by running the bot locally or in Docker,
> then opening a chat with it in Telegram.

---

## Quality Pipeline

See [README.md](../README.md#quality-pipeline-cicd) for the full Quality Gates
description. In short: every push to `main` and every PR runs `black`, `flake8`,
`mypy`, `bandit`, and `pytest` in sequence. The test job only starts if the
quality/security job passes.

## AI-Driven QA Prompts

The repository ships with 6 prompt templates in `../prompts/` for Cline/Obsidian:

- `security_audit_deepseek.md` — Security Auditor
- `mutation_tester_cline.md` — Mutant Killer
- `config_tz_validator.md` — Business-Logic Validator
- `role_pr_reviewer.md` — PR Reviewer
- `role_developer.md` — Developer
- `role_qa_automation.md` — QA Automation Engineer
