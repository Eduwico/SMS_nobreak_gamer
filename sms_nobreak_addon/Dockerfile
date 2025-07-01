# Base adequada para build multiplataforma (usado via build-args)
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.19
FROM $BUILD_FROM

# Configuração de ambiente padrão e comportamento do s6
ENV LANG=C.UTF-8 \
    S6_BEHAVIOUR_IF_STAGE2_FAILS=2

# Instala dependências de sistema e Python
RUN apk add --no-cache \
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

# Copia o script principal e dependências Python
COPY sms_gamer_ups_monitor.py /
COPY requirements.txt /

# Copia arquivos esperados pelo Supervisor (configuração e ícones)
COPY config.yaml icon.png logo.png ./

# Copia os arquivos do serviço (inclui rootfs/run como /run)
COPY rootfs/run /run

# Instala dependências do Python
RUN python3 -m pip install --no-cache-dir --break-system-packages -r /requirements.txt

# Garante que o script de inicialização seja executável (s6-entrypoint)
RUN chmod +x /run

# Define a versão (recebida via build args, usada no metadata e logs)
ARG TAG
ENV ADDON_VERSION=$TAG

# Metadados OCI e Home Assistant
LABEL \
  io.hass.name="SMS Gamer UPS Monitor" \
  io.hass.description="Monitora e controla nobreak SMS Gamer via MQTT - EXPERIMENTAL" \
  io.hass.type="addon" \
  maintainer="du-costa" \
  org.opencontainers.image.title="SMS Gamer UPS Monitor" \
  org.opencontainers.image.description="Home Assistant add-on para monitoramento de nobreak SMS Gamer" \
  org.opencontainers.image.source="https://github.com/du-costa/sms_nobreak_serial" \
  org.opencontainers.image.licenses="GPL-3.0"

# Executa o init padrão do s6-overlay
ENTRYPOINT ["/init"]
