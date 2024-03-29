Building and releasing the GDPR API Tester
==========================================

Update version number in `VERSION` file.

# GitHub package

Create GitHub personal access token. See [GitHub documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-in-a-github-actions-workflow).

```shell
export CR_PAT=[Github Access token]
echo $CR_PAT | docker login ghcr.io -u [GitHub username] --password-stdin

docker build -t profile-gdpr-api-tester .
docker push profile-gdpr-api-tester:latest ghcr.io/city-of-helsinki/profile-gdpr-api-tester:$(cat VERSION)
docker push profile-gdpr-api-tester:latest ghcr.io/city-of-helsinki/profile-gdpr-api-tester:latest
```


# Pypi

Install build requirements (replace `<os>` with your operating system)

```shell
pip install -r requirements.txt -r requirements-build.<os>.txt
```

Build the python distribution. The results will be in the [project_root]/dist-directory.

```shell
python -m build
```

Upload to [Test PyPI](https://test.pypi.org/project/gdpr-api-tester/) and verify everything looks ok there.

```shell
twine upload -r testpypi dist/*
```

Upload to PyPI proper

```shell
twine upload dist/*
```
