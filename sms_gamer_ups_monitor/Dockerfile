ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.19
FROM $BUILD_FROM

ENV LANG=C.UTF-8 \
    S6_BEHAVIOUR_IF_STAGE2_FAILS=2

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema e Python
RUN apk update && apk add --no-cache \
    python3 \
    py3-pip \
    py3-setuptools \
    py3-wheel \
    py3-paho-mqtt \
    build-base \
    linux-headers \
    libffi-dev \
    openssl-dev \
    python3-dev \
    && rm -rf /var/cache/apk/*

# Copia os arquivos do projeto
COPY sms_gamer_ups_monitor.py /app/
COPY requirements.txt /app/

# Copia arquivos do add-on esperados pelo Supervisor
COPY config.yaml icon.png logo.png ./
COPY rootfs/ /

# Instala dependências Python
RUN python3 -m pip install --no-cache-dir --break-system-packages -r requirements.txt

# Permissão para o serviço s6
RUN chmod +x /etc/services.d/sms/run

# Define versão via argumento
ARG TAG
ENV ADDON_VERSION=$TAG

# Metadados
LABEL \
  io.hass.name="SMS Gamer UPS Monitor" \
  io.hass.description="Monitora e controla nobreak SMS Gamer via MQTT - EXPERIMENTAL" \
  io.hass.type="addon" \
  maintainer="du-costa" \
  org.opencontainers.image.title="SMS Gamer UPS Monitor" \
  org.opencontainers.image.description="Home Assistant add-on para monitoramento de nobreak SMS Gamer" \
  org.opencontainers.image.source="https://github.com/du-costa/sms_nobreak_serial" \
  org.opencontainers.image.licenses="GPL-3.0"
