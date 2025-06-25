# Dockerfile melhorado para SMS Gamer UPS Monitor
# Baseado nas melhores práticas para add-ons do Home Assistant

ARG BUILD_FROM
FROM $BUILD_FROM

# Instala dependências do sistema necessárias (como pip)
RUN apk add --no-cache py3-pip

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências Python
# Fazendo isso primeiro para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o script principal
COPY sms_gamer_ups_monitor.py .

# Copia o script de execução do add-on e o torna executável
COPY run.sh .
RUN chmod +x run.sh

# Adiciona labels para metadados do container
LABEL \
    io.hass.name="SMS Gamer UPS Monitor" \
    io.hass.description="Monitora e controla nobreak SMS Gamer via MQTT" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}" \
    maintainer="Eduwico" \
    org.opencontainers.image.title="SMS Gamer UPS Monitor" \
    org.opencontainers.image.description="Home Assistant add-on para monitoramento de nobreak SMS Gamer" \
    org.opencontainers.image.source="https://github.com/Eduwico/SMS_nobreak_gamer" \
    org.opencontainers.image.licenses="GPL-3.0"

# Define o comando padrão para executar o script run.sh
CMD ["./run.sh"]
