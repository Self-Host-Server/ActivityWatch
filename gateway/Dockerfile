FROM node:22-slim AS assets

WORKDIR /build
RUN npm install --no-save sass@1.102.0

COPY scss ./scss
RUN npx sass scss/login.scss static/css/login.css --style=compressed --no-source-map

FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY templates ./templates
COPY --from=assets /build/static ./static

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
