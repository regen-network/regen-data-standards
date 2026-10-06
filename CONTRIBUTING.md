# Contributing

Read [AGENTS.md](AGENTS.md) first. It holds the pre-PR checklist (§1), the rules for linking schemas
and ADRs (§2), and the review tags and response convention (§4). This file covers how to shape a
pull request so it can be reviewed.

Merging needs one approval and passing CI ([#69](https://github.com/regen-network/regen-data-standards/issues/69)).
This repository squash-merges and deletes the merged branch.

## Titles and branches

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for PR titles, for example
`feat(schema): add the C06 claim schema`. The squash commit on `main` takes the PR title.

Name branches `<type>/<issue-number>-<short-description>`, for example `feat/73-attestation-evidence-c06`.
With no issue, leave out the number.

## One problem per pull request

A PR solves one underlying problem. Include everything that problem needs: schema, regenerated
output, examples and docs. Put an unrelated fix, cleanup or refactor in its own PR, even if it is
small and useful. Closely related fixes can share a PR if the description says why.

Start the description with the problem in one or two sentences. A reviewer who reads only that should
know why the PR exists.

A large diff is not a problem by itself. A PR that mixes unrelated changes is.

## Stacked pull requests

When one change depends on another that is still in review, stack them:

1. Base the dependent PR on the parent's branch, not on `main`.
2. Name the parent and any children in the description.
3. When a parent is rebased or force-pushed, rebase each child onto the new parent:

   ```sh
   git fetch origin
   git rebase --onto origin/<parent-branch> <old-parent-tip> <child-branch>
   git push --force-with-lease
   ```

   `<old-parent-tip>` is the commit just below your first own commit. Find it with
   `git log --oneline origin/main..<child-branch>`. If you fetched the parent before it was rebased,
   `origin/<parent-branch>@{1}` also names it.

4. Before you request review, open **Files changed** and check it shows only your change. If it shows
   the parent's commits, the child needs the rebase in step 3.
5. Merge from the bottom of the stack up. After a parent is squash-merged and its branch deleted,
   GitHub retargets the child to the parent's base. The child still holds the parent's original
   commits, which are not on `main`, so rebase it the same way:
   `git rebase --onto origin/main <old-parent-tip> <child-branch>`, then force-push.

## Generated files

Do not edit generated files by hand. Change the source and regenerate (see
[schema/README.md](schema/README.md)). `schema/src/taxonomy.yaml` is mixed: edit its enums by hand,
but let `make -C schema gen-taxonomy` add the taxonomy terms.

Commit regenerated output in a separate commit, for example `chore(schema): regenerate examples`, so a
reviewer can read the source change first.

[.gitattributes](.gitattributes) marks generated paths so GitHub collapses them in PR diffs. When you
add a new generated output, add its path there.

## Evidence

Say how you established the problem, how you checked the change, and what you saw. Give the commands
you ran and their results. Say what you could not check. "Tests pass" on its own does not show that
the change works. The [pull request template](.github/pull_request_template.md) has a section for each.

## Drafts

Opening a draft does not request a review. Say in the description what feedback you want and from
whom, and request those reviewers or mention them. Otherwise the draft may not be seen.
