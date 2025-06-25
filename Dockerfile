# Dockerfile melhorado para SMS Gamer UPS Monitor
# Baseado nas melhores práticas para add-ons do Home Assistant

ARG TARGETARCH
FROM ghcr.io/home-assistant/${TARGETARCH}-base:latest

# Instala dependências do sistema necessárias para Python e compilação
# Inclui pacotes comuns para compilação de extensões Python e acesso a dispositivos
RUN apk update && apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    build-base \
    libffi-dev \
    openssl-dev \
    # Adicionais que podem ser necessários para certas extensões C ou interações de baixo nível
    # Mesmo que pyserial seja Python puro, ele interage com o sistema de arquivos e dispositivos
    # zlib-dev (comum para compressão/descompressão)
    # udev-dev (para algumas interações com dispositivos, embora menos comum para pyserial diretamente)
    && rm -rf /var/cache/apk/*

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências Python
# Fazendo isso primeiro para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copia o script principal
COPY sms_gamer_ups_monitor.py .

# Copia o script de execução do add-on e o torna executável
COPY run.sh .
RUN chmod +x run.sh

# Adiciona labels para metadados do container
LABEL \
    io.hass.name="SMS Gamer UPS Monitor" \
    io.hass.description="Monitora e controla nobreak SMS Gamer via MQTT" \
    io.hass.type="addon" \
    maintainer="Eduwico" \
    org.opencontainers.image.title="SMS Gamer UPS Monitor" \
    org.opencontainers.image.description="Home Assistant add-on para monitoramento de nobreak SMS Gamer" \
    org.opencontainers.image.source="https://github.com/Eduwico/SMS_nobreak_gamer" \
    org.opencontainers.image.licenses="GPL-3.0"

# REMOVIDAS AS LINHAS COM io.hass.arch e io.hass.version

# Define o comando padrão para executar o script run.sh
CMD ["./run.sh"]
