# GitHub Repo Protocol

When Snehasis gives you a bare GitHub URL (a repo, or just an org/topic search), follow this exactly.

## If it's a specific repo URL
1. Clone or fetch it — do not just skim the README.
2. Check: last commit date, open issues, license, dependency count, whether it actually builds.
3. Report back in plain terms: what it does, whether it's actively maintained, whether the license allows commercial use in this project, and how it would plug into `ARCHITECTURE.md`.
4. Do not merge it into the project until Snehasis confirms — propose first, integrate second.

## If it's a general ask ("find me the best X repo")
1. Search for 3-5 real candidates.
2. Compare them on: stars/activity (recency matters more than star count), license, how actively maintained, how well it fits the stack in `ARCHITECTURE.md`.
3. Recommend one, explain why, name the runner-up and why it lost.
4. Wait for a go-ahead before pulling it in.

## Once approved
1. Add it as a proper dependency (package manager), not a copy-pasted folder, unless it needs to be vendored/modified.
2. Log it in `INTEGRATIONS.md` with the same fields as any other integration.
3. Log the decision in `DECISIONS.md` (which repo, why, what the alternative was).
4. Never bring in a repo with a license that blocks commercial use without flagging it first — this is a hard stop, not a suggestion.

## Ground rule
Real, working integration only. If a repo needs real customization to fit, say so and scope it as its own task in `TASKS.md` — never paper over a broken integration with placeholder/fake code that looks like it works.
