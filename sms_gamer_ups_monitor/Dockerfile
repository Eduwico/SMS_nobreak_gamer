ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.19
FROM $BUILD_FROM

ENV LANG C.UTF-8
ENV S6_BEHAVIOUR_IF_STAGE2_FAILS=2

# Define diretório de trabalho para o app
WORKDIR /app

# Copia o script principal para /app
COPY sms_gamer_ups_monitor.py /app/

# Copia o requirements.txt da raiz para o diretório atual (/app)
COPY requirements.txt /app/

# Copia arquivos do add-on esperados pelo Supervisor para a raiz do container
COPY config.yaml icon.png logo.png ./

# Copia estrutura s6-overlay para o sistema
COPY rootfs/ /

# Instala dependências Python
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Garante permissão de execução ao serviço do S6 Overlay
RUN chmod +x /etc/services.d/sms/run

# Define versão via argumento/tag
ARG TAG
ENV ADDON_VERSION=$TAG

# Metadados da imagem
LABEL \
  io.hass.name="SMS Gamer UPS Monitor" \
  io.hass.description="Monitora e controla nobreak SMS Gamer via MQTT - EXPERIMENTAL" \
  io.hass.type="addon" \
  maintainer="du-costa" \
  org.opencontainers.image.title="SMS Gamer UPS Monitor" \
  org.opencontainers.image.description="Home Assistant add-on para monitoramento de nobreak SMS Gamer" \
  org.opencontainers.image.source="https://github.com/du-costa/sms_nobreak_serial" \
  org.opencontainers.image.licenses="GPL-3.0"
