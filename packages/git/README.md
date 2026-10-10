# repolens-git

A thin, safe wrapper around the local `git` binary.

- Every call runs via `subprocess.run([...])` with an explicit argument
  list -- never `shell=True`, never string-interpolated into a shell
  command -- so a file path or branch name can never be used for shell
  injection.
- File paths passed in are validated against the repository root with
  `repolens_shared.paths.resolve_within_root` before being handed to git.
- `repolens_git` never invents history. `file_history`/`blame`/
  `commit_details` return exactly what `git log`/`git blame`/`git show`
  report; if a path has no history (e.g. untracked, or the repo has no
  commits), callers get an empty list, not a guess.
- "Why was this changed?" must be answered from real commit messages only.
  `repolens_git` supplies the messages; it does not interpret or summarize
  intent -- that's for the Q&A layer to do (or decline to do, if the
  message doesn't say).
