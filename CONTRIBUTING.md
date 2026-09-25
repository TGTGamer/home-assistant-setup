# Contributing

Thanks for helping. This is a personal home setup, so issues and small pull
requests are the best fit.

## TGTGamer Cooperation Commitment

If you use this work and improve it, please offer the improvement back as a
pull request or issue, credit the project where you build on it, and raise
problems here before working around them in a fork.

## How to contribute

1. Run `scripts/agent-setup.sh` (or `scripts/agent-setup.ps1`).
2. Make the change with tests; never delete a failing test to get green.
3. Run `pnpm verify`. New source files need the licence header:
   `pnpm house:fix` adds it.
4. Commit with `type(scope): summary` messages, signed off for the
   [Developer Certificate of Origin](https://developercertificate.org/)
   (`git commit -s`).
5. Open a pull request describing what changed and why.

By contributing you agree your work is licensed under the repository's
[FCL-1.0-MIT licence](LICENSE).
