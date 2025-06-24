#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Add-on: SMS Gamer UPS Monitor
# This script starts the Python monitoring script with configurations from the add-on options.
# ==============================================================================

# Read add-on options using bashio
SERIAL_PORT=$(bashio::config "serial_port")
POLL_INTERVAL=$(bashio::config "poll_interval")
MQTT_BROKER=$(bashio::config "mqtt_broker")
MQTT_PORT=$(bashio::config "mqtt_port")
MQTT_USERNAME=$(bashio::config "mqtt_username")
MQTT_PASSWORD=$(bashio::config "mqtt_password")

bashio::log.info "Iniciando SMS Gamer UPS Monitor..."
bashio::log.info "Porta Serial: ${SERIAL_PORT}"
bashio::log.info "Intervalo de Leitura: ${POLL_INTERVAL}s"
bashio::log.info "Broker MQTT: ${MQTT_BROKER}:${MQTT_PORT}"
bashio::log.info "Usuário MQTT: ${MQTT_USERNAME}"

# Execute o script Python, passando as configurações como argumentos
python3 sms_gamer_ups_monitor.py \
    --port "${SERIAL_PORT}" \
    --interval "${POLL_INTERVAL}" \
    --mqtt-broker "${MQTT_BROKER}" \
    --mqtt-port "${MQTT_PORT}" \
    --mqtt-username "${MQTT_USERNAME}" \
    --mqtt-password "${MQTT_PASSWORD}" \
    --mqtt # Ativa o modo MQTT do script
