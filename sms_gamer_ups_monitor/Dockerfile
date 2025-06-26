# Dockerfile melhorado para SMS Gamer UPS Monitor
# Baseado nas melhores práticas para add-ons do Home Assistant

ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest

ARG BUILD_FROM 
# <--- Mude de TARGETARCH para BUILD_FROM
FROM $BUILD_FROM 
# <--- Use o argumento BUILD_FROM aqui

# Instala dependências do sistema necessárias para Python e compilação
# Inclui pacotes comuns para compilação de extensões Python e acesso a dispositivos
RUN apk update && apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    build-base \
    libffi-dev \
    openssl-dev \
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
    maintainer="du-costa" \
    org.opencontainers.image.title="SMS Gamer UPS Monitor" \
    org.opencontainers.image.description="Home Assistant add-on para monitoramento de nobreak SMS Gamer" \
    org.opencontainers.image.source="https://github.com/du-costa/sms_nobreak_serial" \
    org.opencontainers.image.licenses="GPL-3.0"

# Define o comando padrão para executar o script run.sh
CMD ["./run.sh"]
