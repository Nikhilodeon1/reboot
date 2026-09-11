# Pre-registration evidence

Anonymized exports of the two commits that fix the order of the detector 5
pre-registration and its external-validation code.

| Patch | Commit | Date | Content |
|---|---|---|---|
| `0001-preregistration.patch` | `63f5d95a8a8ea9d86f8ab16409f6e62c27af7bb1` | 2026-08-06 00:34:20 -0700 | adds `PREREGISTRATION.md` |
| `0002-external-validation-code.patch` | `1600d91071cf97307924d4b1c85482b4d894eef9` | 2026-08-06 01:03:15 -0700 | adds `variant_a` / `variant_b`, the external testbed and their tests; parent is `63f5d95` |

`detectors/PREREGISTRATION.md` is identical in content to the file added by
`63f5d95`. The only later commit touching it moved the directory without changing
the file.

## Changes for anonymity

- Author name and email replaced with `Anonymous`.
- The package directory is rewritten to its current name, `detectors/`,
  including in import lines.

Diffs, dates and commit messages are otherwise unchanged.

## Limits

Patch dates are author-supplied metadata and cannot be verified from this
repository. The full hashes above are a commitment: a git hash covers the
commit's author, timestamp, content and parent, so the original history released
with the de-anonymized repository must reproduce them.
