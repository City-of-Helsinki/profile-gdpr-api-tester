FROM python:3.10-slim

LABEL org.opencontainers.image.source=https://github.com/City-of-Helsinki/profile-gdpr-api-tester
LABEL org.opencontainers.image.description="Helsinki Profile GDPR API Tester"
LABEL org.opencontainers.image.licenses=MIT

RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends rlwrap

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

COPY /gdpr_api_tester /app/gdpr_api_tester

EXPOSE 8888

# The sleep is needed to make rlwrap work. Without the sleep rlwrap can't determine the terminal dimensions.
# See this issue for more information: https://github.com/moby/moby/issues/28009
CMD sleep 0.1; rlwrap python -m gdpr_api_tester
