# Releasing

## Branches and versions

`develop` is the default and PR branch; `main` is the release branch. Work on a feature
branch named after the GitHub issue (`3-update-nyx-bridge-dependency`).

The version lives in `VERSION`. `make update-version` copies it into `pyproject.toml`;
`extension/blender_manifest.toml` has its own `version` that must be kept equal, or
`make extension` stops. Add a `v<version>` section at the top of `CHANGELOG.rst`, one
bullet per user-visible change with the issue number where there is one.

nyx-bridge-blender depends on `sowwic-nyx-bridge`. When a new nyx-bridge release is
needed, raise the minimum in `pyproject.toml`, run `uv lock` and add a changelog bullet.
The extension zip bundles the version `uv.lock` holds.

## Release

1. Update `CHANGELOG.rst`, `VERSION` (`make update-version`) and the manifest version,
   commit on `main`.
2. Run

   ```bash
   make release VERSION=1.2.3 [RELEASE_TITLE="..."]
   ```

It tags `main`, pushes and merges back into `develop`. The tag triggers
`.github/workflows/release.yml`, which creates the GitHub release from the changelog
section.

## CI

Workflows in `.github/workflows/` are thin callers of the shared ones in
`sowwic/gh-workflows`: tests (see [Testing](testing.md#ci)), lint, docs deployment to
GitHub Pages and the release. Dependabot opens update PRs against `develop`.
