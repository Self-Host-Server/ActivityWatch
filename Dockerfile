FROM debian:bookworm-slim

ARG AW_VERSION=0.13.2

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN curl -fsSL -o aw.zip \
      "https://github.com/ActivityWatch/activitywatch/releases/download/v${AW_VERSION}/activitywatch-v${AW_VERSION}-linux-x86_64.zip" \
    && unzip aw.zip \
    && rm aw.zip \
    && apt-get purge -y curl unzip \
    && apt-get autoremove -y

RUN useradd -m -u 1000 aw \
    && mkdir -p /config \
    && chown -R aw:aw /config
USER aw

# Consolidate aw-server's config + data dirs into one mountable path.
ENV XDG_CONFIG_HOME=/config
ENV XDG_DATA_HOME=/config

EXPOSE 5600

ENTRYPOINT ["/app/activitywatch/aw-server/aw-server", "--host", "0.0.0.0", "--cors-origins", "*"]
