# Git Workflow Guide

A practical guide for working on this project as a small team. Covers everything from starting a new task to getting your work merged into `main`.

## The Mental Model

Three things to keep straight in your head:

1. **`main`** is the shared, "blessed" version of the project. Everyone pulls from it; nobody pushes directly to it.
2. **Branches** are your personal workspace for a single task. You make changes here without affecting anyone else.
3. **Pull requests (PRs)** are how branches get merged back into `main`. They're created and merged on GitHub, not in the terminal.

The basic cycle: **branch → work → commit → push → PR → merge → clean up**.

## Setup (one time, per machine)

```
git clone <repo-url>
cd <repo-folder>
```

Configure your identity if you haven't yet:

```
git config --global user.name "Your Name"
git config --global user.email "you@stanford.edu"
```

## The Standard Workflow

### 1. Start a new task — make a branch

Always start from an up-to-date `main`. Otherwise you'll branch off old code and have merge headaches later.

```
git checkout main
git pull origin main
git checkout -b descriptive-branch-name
```

`git checkout -b` creates a new branch and switches to it. Name it after what you're doing: `add-curvature-fn`, `fix-mses-timeout`, `bayesian-opt`, etc. Avoid naming branches after yourself — branches should be named for content so a teammate can pick them up if needed.

### 2. Work and commit incrementally

Make changes. Commit when you reach a natural stopping point — a working feature, a passing test, end of a session. Commits are cheap; do them often.

```
git status                   # see what's changed
git add <filename>           # stage specific files
git add .                    # stage everything (use carefully)
git commit -m "short description of the change"
```

**Commit message style:** present-tense verb + what changed. "add curvature function", "fix MSES timeout handling", "update README". Keep them short but specific.

### 3. Push your branch to GitHub

The first time you push a new branch:

```
git push -u origin <branch-name>
```

The `-u` sets up tracking — after that, you can just say `git push` and `git pull` without specifying the branch name.

Push regularly (at least daily) so your work is backed up on GitHub even if your laptop dies.

### 4. Open a Pull Request (PR)

When your task is done and you're ready for review/merge:

1. Go to the repo on GitHub
2. You'll see a yellow banner offering "Compare & pull request" — click it
3. Confirm the PR is going `<your-branch> → main`
4. Write a description: what does this change, anything reviewers should look at?
5. Click "Create pull request"

If a teammate is doing review, request one. They'll comment on the PR or approve it.

### 5. Merge the PR

On the PR page, click "Merge pull request" → "Confirm merge". For a class project, "Create a merge commit" (the default) is fine.

### 6. Clean up locally

After the merge, your local `main` is out of date and your feature branch is no longer needed:

```
git checkout main
git pull origin main
git branch -d <branch-name>      # delete local branch (safe — refuses if unmerged)
git fetch --prune                # clean up references to deleted remote branches
```

GitHub also offers a "Delete branch" button on the merged PR page — click it to clean up the remote.

## Working on Multiple Branches in Parallel

You can have several branches going at once — for example, one for a feature you're building and one for a bug fix. The rule: **finish what you're committing before switching branches**.

```
git status                   # check for uncommitted changes
# either commit them, or:
git stash                    # temporarily shelve them
git checkout other-branch    # switch
# do stuff on other-branch, commit, switch back
git checkout original-branch
git stash pop                # restore shelved changes
```

If you switch branches with uncommitted changes, git will usually try to bring them along — fine if there's no conflict, but messy if there is. Commit or stash first, every time.

## Keeping Your Branch Up to Date with `main`

If your branch has been around for a while and `main` has moved forward (teammates merging things), bring those changes into your branch. Otherwise, when you eventually open a PR, you'll have merge conflicts.

```
git checkout main
git pull origin main
git checkout your-branch
git merge main
git push
```

This pulls the latest `main` into your branch. Do this every few days, or whenever a teammate's PR gets merged.

## Common Situations

### "I'm not sure what state I'm in"

```
git status              # what's changed, what's staged, what branch
git branch              # what branches exist locally; * marks current
git log --oneline -5    # last 5 commits on current branch
```

These three commands answer 90% of "wait, what's going on" questions.

### "I made changes but haven't committed and want to discard them"

```
git restore <filename>    # discard changes to a specific file
git restore .             # discard ALL uncommitted changes (careful)
```

### "I committed but realized I want to change the message"

```
git commit --amend -m "better message"
```

Only safe if you haven't pushed yet. Don't amend pushed commits.

### "I want to undo my last commit but keep the changes"

```
git reset --soft HEAD~1
```

This rolls back one commit but keeps your file changes staged. You can then re-commit.

### "I want to see what changed in a file before I commit"

```
git diff <filename>            # unstaged changes
git diff --staged <filename>   # staged changes
```

### "I pulled and got merge conflicts"

```
git status                     # tells you which files conflict
```

Open each conflicted file. You'll see markers like:

```
<<<<<<< HEAD
your version
=======
the version from main
>>>>>>> main
```

Edit the file to keep what you want (delete the markers), save, then:

```
git add <file>
git commit
```

For Jupyter notebooks (`.ipynb`), don't try to manually merge — pick one version wholesale:

```
git checkout --ours <file>     # keep your branch's version
git checkout --theirs <file>   # keep the incoming version
git add <file>
git commit
```

### "I want to start over and bail out of a messy merge"

```
git merge --abort
```

This cancels an in-progress merge and puts you back where you were before. No harm done.

### "I accidentally deleted a file and committed the deletion"

Find the commit where it last existed:

```
git log --diff-filter=D --summary -- <filename>
```

Restore from a previous commit:

```
git checkout <commit-sha> -- <filename>
git add <filename>
git commit -m "restore <filename>"
```

### "git is showing a `:` and I can't type"

You're stuck in a pager (`less`). Press `q` to exit.

## Things to Avoid

- **Never push directly to `main`.** Always go through a branch and PR. This protects everyone from accidental breakage.
- **Don't commit large files** (datasets, MSES output, generated PDFs, log files, virtual environments). Use `.gitignore` to exclude them. The repo gets clogged otherwise.
- **Don't `git push --force` on shared branches.** If you must rewrite history (e.g., after rebase), use `--force-with-lease` and only on your own branches that no one else is working on.
- **Don't commit secrets.** API keys, passwords, anything sensitive — once committed, they're effectively permanent in git history. If it happens, change the secret immediately.
- **Don't make giant commits.** "Initial commit" with 50 files at once is hard to review. Smaller, focused commits are easier to understand and revert if needed.
- **Don't merge your own PR without at least skimming the diff.** It catches obvious mistakes.

## What `.gitignore` Should Cover for This Project

Make sure these are in `.gitignore` so nobody accidentally commits them:

```
# Virtual environments
f1env/
venv/
.venv/

# Python build artifacts
__pycache__/
*.pyc
.ipynb_checkpoints/

# MSES output
*.bdamp.*
*.fort.*

# Editor / OS
.vscode/
.DS_Store
Thumbs.db

# Generated outputs
eval_log.csv
*.pkl
results/
```

## Quick Reference: The Lifecycle in 10 Commands

```
git checkout main                         # 1. start from main
git pull origin main                      # 2. ensure it's up to date
git checkout -b my-task                   # 3. branch
# ... edit files ...
git status                                # 4. see what changed
git add <files>                           # 5. stage
git commit -m "what I did"                # 6. commit
git push -u origin my-task                # 7. push (first time only needs -u)
# ... open PR on GitHub, get reviewed, merge ...
git checkout main                         # 8. back to main
git pull origin main                      # 9. pull merged work
git branch -d my-task                     # 10. delete local branch
```

That's the full loop. Memorize this and you're 95% of the way there.

## When Stuck

If you're confused or have an unclear error, **stop and run `git status`**. It almost always tells you what state you're in and what to do next. Most git problems look scarier than they are.

If `git status` doesn't help, three rules of thumb:

1. **Don't run commands you don't understand.** Especially `git reset --hard`, `git push --force`, or anything with `--force` in it. Ask first.
2. **You can almost always recover.** Git keeps history of nearly everything. Even "deleted" branches and commits can be found via `git reflog`.
3. **`git merge --abort`, `git rebase --abort`, and `git reset --hard ORIG_HEAD`** are escape hatches that put you back to a known good state when something goes sideways mid-operation.
