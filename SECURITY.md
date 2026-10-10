# Security Policy

## Reporting a vulnerability

If you believe you've found a security vulnerability in RepoLens, please
report it privately rather than opening a public issue:

- Preferred: use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability)
  for this repository (Security tab -> "Report a vulnerability").
- Alternatively, open a draft security advisory, or contact a maintainer
  directly if you can't access either of the above.

Please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce it (a minimal repository/config that triggers it, if
  applicable).
- The version/commit you tested against.

We'll acknowledge your report, investigate, and aim to keep you updated on
progress toward a fix. Please give us a reasonable window to address the
issue before any public disclosure.

## Supported versions

RepoLens does not yet have tagged releases; security fixes land on `main`.
Once versioned releases begin, this section will list which versions
receive security updates.

## Scope

In scope:

- The packages under `packages/` and apps under `apps/` in this repository.

Out of scope:

- Vulnerabilities in third-party dependencies -- please report those
  upstream (we'll still appreciate a heads-up so we can update).
- Issues that require an attacker to already have arbitrary code execution
  on the machine running RepoLens.

## What this project does and doesn't protect against

See [`docs/security.md`](docs/security.md) for a description of RepoLens's
actual security properties (path-traversal protections, subprocess
discipline, secret-file exclusion, prompt-injection containment) and known
gaps (no built-in authentication -- RepoLens is designed for local,
single-user use).
