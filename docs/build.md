Building and releasing the GDPR API Tester
==========================================

Version is managed in `pyproject.toml` and updated by Release Please.

# GitHub package

Create GitHub personal access token. See [GitHub documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-in-a-github-actions-workflow).

```shell
export CR_PAT=[Github Access token]
echo $CR_PAT | docker login ghcr.io -u [GitHub username] --password-stdin

IMAGE=ghcr.io/city-of-helsinki/profile-gdpr-api-tester
VERSION=$(awk -F '"' '/^version = "/ {print $2; exit}' pyproject.toml)

docker build -t profile-gdpr-api-tester .
docker tag profile-gdpr-api-tester "$IMAGE:$VERSION"
docker tag profile-gdpr-api-tester "$IMAGE:latest"
docker push "$IMAGE:$VERSION"
docker push "$IMAGE:latest"
```


# Pypi

Sync build dependencies

```shell
uv sync --group build
```

Build the python distribution. The results will be in the [project_root]/dist-directory.

```shell
uv run hatch build
```

Upload to [Test PyPI](https://test.pypi.org/project/gdpr-api-tester/) and verify everything looks ok there.

```shell
uv run twine upload -r testpypi dist/*
```

Upload to PyPI proper

```shell
uv run twine upload dist/*
```

## Trusted publishing (GitHub Actions)

This repository uses trusted publishing (OIDC) in GitHub Actions for PyPI and TestPyPI uploads.

Before publishing, configure trusted publishers in PyPI and TestPyPI project settings:

- Owner: `City-of-Helsinki`
- Repository: `profile-gdpr-api-tester`
- Workflow name: `publish.yml` for PyPI and `test_release.yml` for TestPyPI
- Environment: `pypi` for both workflows

After setup:

- `publish.yml` runs on pushes to `main`, on a daily schedule, and manually via workflow dispatch.
- `test_release.yml` can be run manually to publish to TestPyPI.
