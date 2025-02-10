FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV JENKINS_USERNAME=jenkins_user \
    JENKINS_API_TOKEN=default_token \
    LOG_LEVEL=INFO

CMD ["python", "src/main.py"]