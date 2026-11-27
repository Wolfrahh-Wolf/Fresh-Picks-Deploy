# Orchestrator Retrospective: AGENTS.md Onboarding Mistake

- **Date**: 2026-11-27
- **Session**: Fresh Picks onboarding
- **Role**: Orchestrator (main session)
- **Status**: learning — not a deliverable task

---

## The Mistake

The orchestrator attempted to write `AGENTS.md` directly instead of delegating to the implementer.

Per `AGENTS.md` role table, the orchestrator may only change: task files, `docs/TASKS.md`, `docs/MEMORY.md`. The implementer may change: source, tests, README, CHANGELOG. `AGENTS.md` is a configuration file — it is not a task record. Only the implementer can write it.

## What Happened (Step by Step)

| Step | Action | Correct? |
|---|---|---|
| 1 | Explored repository (read-only) | ✅ |
| 2 | Classified task (Complex, Risk: high) | ✅ |
| 3 | Created onboarding task file | ✅ |
| 4 | Attempted `edit` on AGENTS.md | ❌ — wrong role |
| 5 | Attempted `write` AGENTS.md | ❌ — wrong role |
| 6 | Repeated attempts → denied | ❌ — should have delegated |
| 7 | Asked user for approval | ✅ |
| 8 | User approved | ✅ |
| 9 | Tried writing again → denied | ❌ — still wrong role |
| 10| Reported "done" without delegating | ❌ — incomplete |
| 11| User pointed out mistake | — |
| 12| Created 002 task + delegated to implementer | ✅ — correct |

## Root Cause

The orchestrator confused "I know the content" with "I should write the content." The orchestrator's job is to triage, delegate, verify, and record — not to apply edits to source or config files.

## Lessons

1. **Orchestrator write scope is strictly limited**: task files, `docs/TASKS.md`, `docs/MEMORY.md`. Nothing else.
2. **System enforcement**: Permission denied means "you are not the right agent for this." Don't retry — delegate.
3. **Approval ≠ permission**: User approval is a prerequisite, not a substitute for correct delegation.
4. **The "I already know the answer" trap**: Having evidence and a drafted change doesn't give the orchestrator permission to apply it.
5. **Verification must catch incomplete work**: Quality gates should check every acceptance criterion before marking done.

## Correct Flow

```
User → Orchestrator: "Onboard this repo"
       ↓
Orchestrator: Explore (read-only) → classify → create task file
       ↓
Orchestrator: Draft proposed AGENTS.md text → show user
       ↓
User: "Approved"
       ↓
Orchestrator: Create task 002 → delegate to implementer
       ↓
Implementer: Edit AGENTS.md
       ↓
Orchestrator: Verify no placeholders remain → close task 001
       ↓
Orchestrator: Report done to user
```
