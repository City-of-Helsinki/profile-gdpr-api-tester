FROM python:3.10-slim

LABEL org.opencontainers.image.source=https://github.com/City-of-Helsinki/profile-gdpr-api-tester
LABEL org.opencontainers.image.description="Helsinki Profile GDPR API Tester"
LABEL org.opencontainers.image.licenses=MIT

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

COPY /gdpr_api_tester /app/gdpr_api_tester

EXPOSE 8888

CMD ["python", "-m", "gdpr_api_tester"]
