# Eventiva automation

This integration uses Amp cloud orbs for coding and OpenClaw on the hub for
supervision. The workstation is only an administration client.

Amp's native integrations own event intake for `Resnovas/Eventiva` and Linear
team `EVE`. The OpenClaw supervisor checks known work every five minutes and
reconciles missed events every fifteen minutes. Twenty minutes without useful
activity triggers investigation, not an automatic restart. Recovery uses the
same Amp thread, with at most two attempts per unchanged blocker, thirty
minutes apart. Workers may open PRs; they may not merge or deploy.

## Install on the gateway

Use the **OpenClaw app's terminal** in Home Assistant. The separate Terminal &
SSH app cannot see OpenClaw's private files. Obtain a checkout of this repository
in the OpenClaw app. Node, pnpm, jq and OpenClaw must be installed there.

Set a persistent workspace outside the repository and run the preparation:

```sh
export EVENTIVA_WORKSPACE=/config/eventiva-supervisor
pnpm openclaw:eventiva prepare
```

Preparation creates an isolated agent, installs the instructions, registers
Puck MCP with OAuth, and creates a disabled schedule. It does not start coding
work. Rerunning preserves the ledger, requires the managed schedule to be
disabled, and refuses to adopt an unrelated workspace or duplicate jobs.

In OpenClaw **Settings > MCP**, sign in to `eventiva-puck` using the Amp account
that owns the Eventiva project. Credentials for the MCP connection in a coding
assistant are not automatically shared with the gateway. Follow any exact
redirect/client registration steps requested by Amp. Do not paste tokens into
repository files or chat.

Then queue an observational test:

```sh
pnpm openclaw:eventiva smoke
```

Inspect the run in OpenClaw and the workspace's `smoke-test.json`. The test must
read the project, an EVE issue, repository/PR state and an exact known Amp
thread. Idle threads must remain visible to supervision. Once the reads pass:

```sh
pnpm openclaw:eventiva enable
pnpm openclaw:eventiva status
```

Activation requires a passing smoke test from the last hour. This establishes
read access, not end-to-end webhook correctness. The first live pass inventories
existing work; it must not launch old backlog. Make sure the configured model
and tool policy permit unattended Puck calls for this agent. Never change
unrelated agent policies or disable gateway device authentication to achieve it.

## Verify the complete system

- Read back Amp's actual event subscriptions and repository/team filters. A
  manual mention route does not implement automatic issue-created intake.
- Verify issue creation and actionable-state changes separately. Start with a
  controlled issue and confirm exactly one associated orb.
- Verify a pushed commit or PR head produces one review for that SHA. PR-only
  coverage must not be reported as arbitrary commit-push coverage.
- Replay an event and confirm no duplicate worker or review.
- Simulate a blocked/stopped test job. Confirm the supervisor inspects its
  thread, distinguishes blocked from busy, and resumes the same job only when
  recoverable. Never kill real product work to test this.
- Verify CI failure follow-up, uncertain launch recovery, lost tool access and
  missing/corrupt local state all produce actionable errors.
- Verify a completed turn does not mark Linear done before merge and required
  checks, and that dependency completion can release the next eligible issue.

Record enabled events, subscription IDs and test evidence in private operational
state. Do not put personal identifiers, credentials or webhook URLs in this
repository. Do not claim an event type is active until its configuration and
delivery have both been verified.

## Pause and recover

```sh
pnpm openclaw:eventiva disable
```

This stops future supervisor runs. It does not cancel a currently executing
run, stop existing orbs, or pause Amp's separate event subscriptions. Pause those
subscriptions in Amp as well when a full automation stop is needed.

Keep `state.json` and `control.json` in Home Assistant backups. If state is lost,
pause automation and reconstruct issue/thread/PR associations from Amp and
Linear before enabling it. Do not replace lost state with an empty ledger on a
live system. The previous instruction files are retained as `*.previous` when
preparation updates them.

## References

- [OpenClaw MCP](https://docs.openclaw.ai/tools/mcp)
- [Amp Puck MCP](https://ampcode.com/news/take-puck-with-you)
- [Amp automations and webhooks](https://ampcode.com/docs/orbs/automations)
- [Linear integrations](https://ampcode.com/docs/integrations)
