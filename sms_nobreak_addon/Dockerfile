ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8 \
    S6_BEHAVIOUR_IF_STAGE2_FAILS=2

# Instala dependências
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

# Define o diretório de trabalho para o app
WORKDIR /usr/src/app

# Copia código-fonte e requisitos
COPY sms_gamer_ups_monitor.py ./
COPY requirements.txt ./

# Copia config e ícones (mantidos na raiz por padrão do supervisor)
COPY config.yaml icon.png logo.png /root/

# Copia o script de inicialização do add-on (s6-overlay)
COPY rootfs/run /run
RUN chmod +x /run

# Instala dependências Python
RUN python3 -m pip install --no-cache-dir --break-system-packages -r requirements.txt

# Define a versão como variável de ambiente
ARG TAG
ENV ADDON_VERSION=$TAG

# Metadados OCI
LABEL \
  io.hass.name="SMS Gamer UPS Monitor" \
  io.hass.description="Monitora e controla nobreak SMS Gamer via MQTT - EXPERIMENTAL" \
  io.hass.type="addon" \
  maintainer="du-costa" \
  org.opencontainers.image.title="SMS Gamer UPS Monitor" \
  org.opencontainers.image.description="Home Assistant add-on para monitoramento de nobreak SMS Gamer" \
  org.opencontainers.image.source="https://github.com/du-costa/sms_nobreak_serial" \
  org.opencontainers.image.licenses="GPL-3.0"

ENTRYPOINT ["/init"]
