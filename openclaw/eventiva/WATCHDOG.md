# Five-minute watchdog

Run this procedure once per invocation. The native OpenClaw schedule supplies
the five-minute interval. Do not sleep, create schedules, or leave polling loops.

1. Read `control.json` and `state.json`. Report whether this is a dry run.
   Ask Puck for Eventiva's exact linked threads, including idle, blocked,
   completed, and archived ones, and for the currently configured event
   subscriptions. Do not rely on the active-orbs list alone.
2. For each active job, inspect its latest messages/tool activity, pending
   questions, process/test progress, branch/head SHA, PR and CI. Record the
   evidence and expected next output. Progress includes useful investigation and
   running tests, not only commits. Preserve the previous timestamp when there
   is no new evidence; the observation time is not the progress time.
3. Inspect a job more closely after 20 minutes without useful progress. A
   five-minute check interval is not a five-minute failure threshold. Do not
   interrupt a worker or long-running test just because it has not committed.
4. Classify a suspected stall: still working, waiting on dependency, waiting on
   user approval, credentials/quota failure, failed test/check, stopped worker,
   or unexplained inactivity. Report evidence, never just "stalled".
5. Outside dry-run mode, resume the SAME thread only when evidence establishes
   a recoverable stopped job or actionable test/review failure. Include the
   issue acceptance criteria, latest head SHA, failure evidence and next action.
   Allow at most two recovery attempts per unchanged blocker, at least
   30 minutes apart. Reset the attempt count only after verified new progress.
   Record the attempt before sending. Resolve uncertain sends by inspection.
   Preserve branches and uncommitted work. Never start a replacement blindly.
6. Credentials, policy decisions, budget exhaustion, approval prompts and
   repeated failures require an actionable report with a thread link. Waiting
   on a user is not a recoverable crash. Suppress identical repeated reports;
   report changed blockers or failed monitoring itself.
7. Every 15 minutes, reconcile EVE issue changes, repository pushes, open PR
   heads and CI with native subscriptions and the ledger. Use an overlap window
   and dedupe by issue identity or repository + head SHA. Inspect current state
   rather than relying on event ordering. Do not review the same commit twice.
   A commit in an open PR is reviewed through that PR, not a second push job.
8. On the first reconciliation, inventory existing work and establish the
   activation timestamp. Do not launch the historical backlog. Subsequently,
   eligible new or newly actionable issues must be for the allowed repository,
   have concrete acceptance criteria and no unresolved dependencies. Check
   existing threads/PRs immediately before any launch. Ambiguous, non-code,
   draft, canceled, or already completed issues need no coding job.
9. Recovery launches may fill a missed native event only after Puck confirms
   there is no existing or pending job. Use the project's default mode/model.
   Limit recovery-created implementation work to one active job at a time.
   Do not interfere with separately user-started work.
10. Persist observations and return a concise report of actions, blockers and
    supporting links. If nothing changed, return "No changes". If tool access
    failed, report that failure and do not advance reconciliation checkpoints.

## Dry-run acceptance

When `control.json` has `dryRun: true`, execute only observations. Verify that
Puck can resolve the project, read an EVE issue, read repository/PR state, and
inspect an exact known Eventiva thread (including idle state). Report the
references used, access failures, and intended actions without performing them.
Only after all four reads succeed, write `smoke-test.json` with `ok: true`,
`checkedAt` (UTC ISO timestamp), `project`, `issue`, `repository`, and `thread`.
On any failure write `ok: false` with a non-secret explanation. This smoke test
does not prove webhook delivery, recovery behavior, or end-to-end completion;
those require their own acceptance checks.
