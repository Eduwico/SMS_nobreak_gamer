ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.19
FROM $BUILD_FROM

ENV S6_BEHAVIOUR_IF_STAGE2_FAILS=2

RUN apk update && apk add --no-cache \
    python3 \
    py3-pip \
    build-base \
    libffi-dev \
    openssl-dev \
    python3-dev \
    && rm -rf /var/cache/apk/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sms_gamer_ups_monitor.py /app/
COPY rootfs/ /  # importa estrutura s6-overlay

RUN chmod +x /etc/services.d/sms/run

# Adiciona labels para metadados do container
LABEL \
    io.hass.name="SMS Gamer UPS Monitor" \
    io.hass.description="Monitora e controla nobreak SMS Gamer via MQTT - EXPERIMENTAL" \
    io.hass.type="addon" \
    maintainer="du-costa" \
    org.opencontainers.image.title="SMS Gamer UPS Monitor" \
    org.opencontainers.image.description="Home Assistant add-on para monitoramento de nobreak SMS Gamer" \
    org.opencontainers.image.source="https://github.com/du-costa/sms_nobreak_serial" \
    org.opencontainers.image.licenses="GPL-3.0"

