#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Add-on: SMS Gamer UPS Monitor - Versão Melhorada
# This script starts the Python monitoring script with configurations from the add-on options.
# 
# Melhorias implementadas:
# - Suporte aos novos parâmetros configuráveis (baud_rate, timeout)
# - Não loga informações sensíveis (senhas)
# - Validação básica de parâmetros
# - Logs mais informativos
# ==============================================================================

# Read add-on options using bashio
SERIAL_PORT=$(bashio::config "serial_port")
POLL_INTERVAL=$(bashio::config "poll_interval")
BAUD_RATE=$(bashio::config "baud_rate")
TIMEOUT=$(bashio::config "timeout")
MQTT_BROKER=$(bashio::config "mqtt_broker")
MQTT_PORT=$(bashio::config "mqtt_port")
MQTT_USERNAME=$(bashio::config "mqtt_username")
MQTT_PASSWORD=$(bashio::config "mqtt_password")

bashio::log.info "=========================================="
bashio::log.info "SMS Gamer UPS Monitor - Versão Melhorada"
bashio::log.info "=========================================="
bashio::log.info "Porta Serial: ${SERIAL_PORT}"
bashio::log.info "Intervalo de Leitura: ${POLL_INTERVAL}s"
bashio::log.info "Baudrate: ${BAUD_RATE}"
bashio::log.info "Timeout: ${TIMEOUT}s"
bashio::log.info "Broker MQTT: ${MQTT_BROKER}:${MQTT_PORT}"
bashio::log.info "Usuário MQTT: ${MQTT_USERNAME}"
# Não loga a senha por questões de segurança

# Validação básica de parâmetros
if [[ -z "${SERIAL_PORT}" ]]; then
    bashio::log.fatal "Porta serial não configurada!"
    exit 1
fi

if [[ -z "${MQTT_BROKER}" ]]; then
    bashio::log.fatal "Broker MQTT não configurado!"
    exit 1
fi

if [[ -z "${MQTT_USERNAME}" ]] || [[ -z "${MQTT_PASSWORD}" ]]; then
    bashio::log.warning "Credenciais MQTT não configuradas. Tentando conexão sem autenticação..."
fi

# Verifica se a porta serial existe
if [[ ! -e "${SERIAL_PORT}" ]]; then
    bashio::log.warning "Porta serial ${SERIAL_PORT} não encontrada. Verifique a conexão do dispositivo."
fi

bashio::log.info "Iniciando monitoramento..."

# Execute o script Python, passando as configurações como argumentos
python3 sms_gamer_ups_monitor.py \
    --port "${SERIAL_PORT}" \
    --interval "${POLL_INTERVAL}" \
    --baud-rate "${BAUD_RATE}" \
    --timeout "${TIMEOUT}" \
    --mqtt-broker "${MQTT_BROKER}" \
    --mqtt-port "${MQTT_PORT}" \
    --mqtt-username "${MQTT_USERNAME}" \
    --mqtt-password "${MQTT_PASSWORD}" \
    --mqtt # Ativa o modo MQTT do script
