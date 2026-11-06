# nyx-bridge-blender

![Tests](https://github.com/sowwic/nyx-bridge-blender/actions/workflows/unit_tests.yml/badge.svg)
![Code Quality](https://github.com/sowwic/nyx-bridge-blender/actions/workflows/code_quality.yml/badge.svg)

Description

## Development

```sh
uv sync            # install the project and dev dependencies
make check         # lint + tests
make help          # list all targets
```

## Releasing

1. Add a `v<version>` entry to `CHANGELOG.rst`, update `VERSION` (`make update-version`) and commit on `main`.
2. `make release VERSION=<version>` tags, pushes (triggering the GitHub release workflow) and back-merges into `develop`.
