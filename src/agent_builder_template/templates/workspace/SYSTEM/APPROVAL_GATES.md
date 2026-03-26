# Approval Gates

Stop and seek explicit approval before proceeding when work crosses one of these boundaries.

## Always Escalate

- Major architecture changes
- Final stack choices with long-lived consequences
- External services with account, cost, legal, or security impact
- Authentication, payments, or sensitive data handling
- Destructive data or infrastructure operations
- Large scope expansion beyond the stated intended output
- Deployment to shared or production-like environments

## Usually Escalate

- New dependencies with meaningful maintenance cost
- Shared interface changes that affect multiple parts of the system
- Automation that changes delivery workflow for other contributors

## Not Usually Required

- Small internal improvements within an approved slice
- Low-risk implementation details that do not alter architecture or scope
- Targeted validation work tied directly to the approved task

When in doubt, escalate. Hidden approval debt is more expensive than one extra confirmation.
