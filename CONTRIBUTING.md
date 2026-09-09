# Contributing

## Ticket to merge

```text
Jira ticket -> Ready -> developer starts work -> In Progress
-> feature/bugfix/chore branch -> implementation -> pull request
-> Code Review -> CI/testing -> merge -> Done
```

1. Confirm the Jira ticket is **Ready** before implementation begins. Move it to **In Progress** when you start work.
2. Create a branch from up-to-date `main` using the naming conventions below. Implement the ticket and run the relevant [frontend](README.md#frontend-quality-checks) and [backend](README.md#backend-quality-checks) checks locally.
3. Open a pull request targeting `main`. When it is ready for review, move the ticket to **Code Review**.
4. Address review feedback and verify CI passes. If separate testing is needed after review, move the ticket to **Testing** and record the results in the PR.
5. Merge after review comments are resolved and CI/testing passes. Move the ticket to **Done** only after the change is merged and accepted against its acceptance criteria.

These are contributor conventions, not a claim that Jira transitions or GitHub branch protections are configured.

## Branches and commits

| Work | Branch pattern | Example |
| --- | --- | --- |
| Feature | `feature/GEO-<ticket>-short-description` | `feature/GEO-21-menu-categories` |
| Bug fix | `bugfix/GEO-<ticket>-short-description` | `bugfix/GEO-35-cart-total` |
| Maintenance or setup | `chore/GEO-<ticket>-short-description` | `chore/GEO-13-collaboration-workflow` |

Prefer concise commit messages that reference the Jira ticket:

```text
GEO-21 add menu category endpoint
GEO-35 fix cart total calculation
```

## Pull requests and review

- Reference the Jira ticket and explain what changed.
- Include testing performed and results, including relevant manual checks or any verification limitations.
- Keep each PR focused on one ticket when practical. Do not mix unrelated changes.
- Once multiple developers are active, obtain review from at least one other contributor. Authors should not approve their own PRs. While working solo, still use PRs, inspect the diff, and require passing CI.
- Review for correctness, maintainability, tests, security, and scope. Resolve review comments before merging.

The existing [CI workflow](.github/workflows/ci.yml) runs on PRs targeting `main` and pushes to `main`. Its frontend job runs lint, TypeScript checks, and the production build; its backend job runs Ruff lint, formatting checks, and pytest. Both jobs should pass on the latest PR changes before merge. CI may run while review is in progress; it does not replace review or ticket-specific testing.

## Main and merging

Changes should reach `main` through pull requests; contributors should not normally push directly to `main`.

Prefer **squash merging** normal feature and bug-fix PRs so each Jira ticket has a clean commit on `main`. Use a concise squash commit message referencing the ticket. Preserve meaningful commit history only when there is a clear reason, explained in the PR.
