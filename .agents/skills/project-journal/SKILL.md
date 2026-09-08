---
name: project-journal
description: Update Georgio's engineering journal in docs/project-journal.md from completed work, recent repository changes, or a specified Jira ticket or feature. Use for journal maintenance and recording interview or STAR material, including before a pull request; not for implementing features or generating unsupported resume claims.
---

# Project Journal

Maintain `docs/project-journal.md` as an accurate source for technical interviews, behavioral interviews, STAR stories, resume bullets, and system-design discussions. Resolve paths from the repository root, including when invoked from `frontend/` or `backend/`.

## Inputs and scope

Accept a Jira ticket such as GEO-12, a feature name, the completed work in the conversation, or a request to review recent repository changes. A ticket identifier is optional. Use the supplied scope; do not assume a ticket's contents or completion state from its identifier.

Examples:

- `Use $project-journal for GEO-12.`
- `Use $project-journal to update the journal for the work we just completed.`
- `Run $project-journal before I open this pull request.`

Update only the journal. Do not modify application code, install dependencies, change tickets, open pull requests, or commit changes unless separately and explicitly asked.

## Inspect before writing

1. Read applicable repository instructions and the existing journal, including its latest dated entries and current-status sections.
2. Inspect `git status --short`, staged and unstaged diffs, relevant untracked files, and recent commit history. Read relevant implementation files, dependency manifests, documentation, and available verification results. Use `rg` for targeted searches. Do not read secrets or generated dependency/build trees.
3. Compare this evidence with what the journal already records. Use journal history, ticket references, and commit references where available to establish the previous entry's coverage. Do not equate a clean working tree with no new work, or assume everything in the latest commit is new to the journal. If the baseline is uncertain, state the uncertainty rather than inventing a revision range.
4. Use explicit project context for decisions, motivations, and environment events that code cannot establish. If a necessary fact is missing, ask a focused question or mark it as not recorded; continue with supported facts. Access Jira or GitHub information only when available and relevant; neither service is required to use this skill.
5. Identify meaningful changes: completed behavior, newly adopted tools, new plans or decisions, debugging outcomes, and collaboration changes. If all meaningful information is already covered, leave the journal unchanged and report that there is no journal-worthy change. Do not add filler or a date-only entry.

## Update the relevant sections

Preserve useful content, verified details, existing structure, and historical context. Make focused additions or corrections rather than rewriting the journal. Avoid duplicate stories across repeated invocations. Update current-status summaries when new evidence supersedes them, while keeping earlier accomplishments identifiable as historical.

Date new or substantively updated entries with the actual update date in `YYYY-MM-DD` format. Preserve original entry dates; label later amendments with their update date. Distinguish an event's date from the recording date if they differ or the event date is unknown. Include a supplied ticket or feature name when its relationship to the work is supported.

- **Completed work:** Explain the concrete problem or goal, what changed, and the observed result. Separate implemented, verified, merged, and deployed states; one does not prove the others. Record tests or checks actually run, their outcomes, and material verification limitations. Do not run a broad test suite merely to update documentation or report a check as passing because a test file exists.
- **Planned work and technologies:** Keep planned items separate from completed work. Update the technology list for newly adopted tools only when repository evidence or explicit project context supports adoption. Distinguish a declared dependency from an integrated feature; a transitive dependency alone does not establish deliberate adoption. Keep evaluated-but-not-selected alternatives distinct from plans.
- **Architecture decisions:** Record **Decision**, **Reasoning**, **Alternatives considered**, and **Tradeoffs**. Prefer specific engineering reasoning tied to this project. Do not infer the team's motivation from framework capabilities or invent alternatives that were never considered. Mark unsupported fields as not recorded.
- **Challenges and debugging:** Add a meaningful entry only for an actual investigation or implementation challenge. Use **Problem**, **Investigation**, **Root cause**, **Solution**, **Result**, and **Lesson learned**. Distinguish confirmed causes from hypotheses and resolved problems from open issues. Leave unknown facts explicit rather than completing the narrative with guesses.
- **Project management and collaboration:** Record relevant changes to Jira, Kanban, tickets, branches, pull requests, reviews, or testing workflow. Distinguish a planned process from one actually followed. Do not claim a ticket is Done, a review occurred, or a branch was merged without supporting evidence or explicit context.
- **Interview story:** Add or update a STAR entry only when completed work supports a useful story. Use **Situation**, **Task**, **Action**, **Result**, and **Technical takeaway**. Describe actual contributions and observed outcomes, including qualitative results when no metrics exist. Preserve accurate attribution to contributors and Codex; do not fabricate leadership, conflict, ownership, or business impact.
- **System design and lessons:** Capture concepts demonstrated by the work and connect them to the implementation or decision. Keep future topics as topics to revisit, not demonstrated capabilities. Record only lessons grounded in actual experience or explicit project context; leave unused templates intact.

## Accuracy and final review

- Never invent metrics, technologies, challenges, lessons, or outcomes.
- Never present planned work as implemented, or local verification as production success.
- Keep entries concise but detailed enough to reconstruct the engineering story later. Prefer concrete behavior and reasoning over generic praise.
- Include concise repository paths, commit/PR references, or supplied context attribution where they help substantiate an entry; do not manufacture links or identifiers.
- Review the final journal diff for unsupported claims, contradictions, duplication, and accidental loss of verified details. For an untracked journal, compare against the contents read before editing because ordinary `git diff` will not show it.
- Confirm only the intended journal edits were made, preserving any pre-existing user changes. Report which sections changed, key evidence limitations, or that no meaningful update was needed. Do not commit unless explicitly asked.
