Building and releasing the GDPR API Tester
==========================================


# GitHub package

Create GitHub personal access token. See [GitHub documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-in-a-github-actions-workflow).

```shell
export CR_PAT=[Github Access token]
echo $CR_PAT | docker login ghcr.io -u [GitHub username] --password-stdin

docker build -t profile-gdpr-api-tester .
docker tag profile-gdpr-api-tester ghcr.io/city-of-helsinki/profile-gdpr-api-tester:latest
docker push ghcr.io/city-of-helsinki/profile-gdpr-api-tester:latest
```


# Pypi

TODO


# Binary

TODO Pyoxidizer
