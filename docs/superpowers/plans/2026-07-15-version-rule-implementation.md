# Version Rule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write a lightweight AI rule that keeps the stockTrade system version number consistent through a single authoritative source.

**Architecture:** The rule will define one primary version source, clear bump conditions, and limited sync scope so day-to-day work updates the effective version without forcing historical docs to be rewritten. The implementation only touches the project rule file and uses the already approved design spec as the source of truth.
It will also define the exact SemVer format plus the required release commit message and git tag naming conventions.

**Tech Stack:** Markdown rule file, existing project conventions

---

### Task 1: Write Version Iteration Rule

**Files:**
- Modify: `/Users/zhanghe/MyProjs/trade/eval_sys/.trae/rules/版本迭代.md`
- Reference: `/Users/zhanghe/MyProjs/trade/eval_sys/docs/superpowers/specs/2026-07-15-version-rule-design.md`

- [ ] **Step 1: Replace the placeholder content with an executable rule**

Write rule content that covers:

- primary version source: `stockTrade/backend/app/__init__.py`
- version format: `MAJOR.MINOR.PATCH`
- bump triggers and non-triggers
- `major` / `minor` / `patch` policy
- sync scope for FastAPI version, frontend `package.json`, and displayed version text
- release commit message format: `chore(release): bump version to X.Y.Z`
- git tag format: `vX.Y.Z`
- conflict resolution for inconsistent active version values

- [ ] **Step 2: Review the rule for ambiguity**

Read the final markdown and verify:

- it is concise
- it is directly actionable by an AI agent
- it does not require updating archived docs by default
- it matches the approved lightweight-mode spec

- [ ] **Step 3: Stop without commit**

Do not create a git commit unless the user explicitly asks for one.
