# Release Checklist

Releases are tag-driven. The GitHub Release workflow builds distribution artifacts such as wheels from the tagged commit.

## Before Tagging

- Confirm the working tree contains only intended changes.
- Run `make check`.
- Run `make security`.
- Update `CHANGELOG.md`: move relevant entries from `[Unreleased]` into the release section.
- Confirm README, SECURITY, ADRs and architecture docs still match the implementation.

## Create the Tag

Use semantic versioning and a `vX.Y.Z` tag:

```bash
./tag_version.sh 1.2.3 --dry-run
./tag_version.sh 1.2.3
```

The script creates `v1.2.3`, updates `CHANGELOG.md`, pushes the tag and creates a GitHub Release when `gh` is installed and authenticated.

## GitHub Release

- Check the GitHub Release notes for accuracy.
- Confirm the release workflow completed successfully.
- Download or inspect the built wheel artifacts when needed.

## Future PyPI Publishing

Publishing to PyPI is optional and not required for normal MCP usage. If enabled later, prefer trusted publishing from GitHub Actions and keep package metadata in `pyproject.toml` current.
