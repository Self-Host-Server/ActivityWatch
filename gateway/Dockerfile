FROM node:22-slim AS assets

WORKDIR /build
RUN npm install --no-save sass@1.102.0

COPY scss ./scss
RUN npx sass scss/login.scss static/css/login.css --style=compressed --no-source-map

FROM python:3.13-slim

WORKDIR /app
ENV DJANGO_SECRET_KEY=build-time-placeholder-not-used-at-runtime

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY manage.py .
COPY gatewayproj ./gatewayproj
COPY proxyauth ./proxyauth
COPY scripts ./scripts
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
COPY --from=assets /build/static ./static

RUN python manage.py collectstatic --noinput

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
