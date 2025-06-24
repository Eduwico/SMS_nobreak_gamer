#!/usr/bin/env python3

"""
Script SMS Gamer - Protocolo Real (v7)
Serviço de monitoramento para Home Assistant via MQTT com MQTT Discovery e controle de comandos.
"""

import argparse
import json
import logging
import serial
import struct
import sys
import time
from typing import Dict, Optional, Any
import paho.mqtt.client as mqtt

# --- REMOVIDAS AS CONFIGURAÇÕES HARDCODED AQUI ---
# Elas serão passadas via argumentos de linha de comando ou lidas de variáveis de ambiente.

# Comandos predefinidos com seus parâmetros (cmd_byte, p1, p2, p3, p4)
SMS_GAMER_COMMANDS_PARAMS = {
    'Q': (0x51, 0xFF, 0xFF, 0xFF, 0xFF),
    'I': (0x49, 0xFF, 0xFF, 0xFF, 0xFF),
    'D': (0x44, 0xFF, 0xFF, 0xFF, 0xFF),
    'F': (0x46, 0xFF, 0xFF, 0xFF, 0xFF),
    'G': (0x47, 0x01, 0xFF, 0xFF, 0xFF),
    'M': (0x4D, 0xFF, 0xFF, 0xFF, 0xFF),
    'T': (0x54, 0x00, 0x10, 0x00, 0x00),
    'T1': (0x54, 0x00, 0x64, 0x00, 0x00),
    'T2': (0x54, 0x00, 0xC8, 0x00, 0x00),
    'T3': (0x54, 0x01, 0x2C, 0x00, 0x00),
    'T9': (0x54, 0x03, 0x84, 0x00, 0x00),
    'C': (0x43, 0xFF, 0xFF, 0xFF, 0xFF),
    'L': (0x4C, 0xFF, 0xFF, 0xFF, 0xFF),
    'R': (0x52, 0x00, 0xC8, 0x27, 0x0F),
    "zzz": (0x52, 0x00, 0xC8, 0x0F, 0xEF),
    "zz1": (0x52, 0x01, 0x2C, 0x27, 0x0F),
}

# Configurar logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False


class SMSGamerProtocol:
    def __init__(self, serial_port: str, mqtt_broker: str, mqtt_port: int, mqtt_username: str, mqtt_password: str, mqtt_client_id: str, mqtt_topic_base: str, ha_discovery_prefix: str, device_name: str, device_manufacturer: str, device_model: str, device_sw_version: str):
        self.port = serial_port
        self.serial = None
        self.connected = False
        self.simple_commands_map = {
            'Q': 0x51,
            'I': 0x49,
            'F': 0x46,
        }
        self.mqtt_client = None

        # Configurações MQTT e Discovery agora são atributos da classe
        self.MQTT_BROKER = mqtt_broker
        self.MQTT_PORT = mqtt_port
        self.MQTT_USERNAME = mqtt_username
        self.MQTT_PASSWORD = mqtt_password
        self.MQTT_CLIENT_ID = mqtt_client_id
        self.MQTT_TOPIC_BASE = mqtt_topic_base
        self.HA_DISCOVERY_PREFIX = ha_discovery_prefix
        self.DEVICE_NAME = device_name
        self.DEVICE_MANUFACTURER = device_manufacturer
        self.DEVICE_MODEL = device_model
        self.DEVICE_SW_VERSION = device_sw_version


    def connect(self) -> bool:
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=2400, # BAUD_RATE
                timeout=3 # TIMEOUT
            )
            self.connected = True
            logger.info(f"✅ Conectado ao SMS Gamer em {self.port}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {e}")
            return False

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.connected = False
            logger.info("🔌 Desconectado do SMS Gamer")
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            logger.info("🔌 Desconectado do broker MQTT")

    def calculate_checksum(self, cmd_byte: int, p1: int, p2: int, p3: int, p4: int) -> int:
        return (-1 * (cmd_byte + p1 + p2 + p3 + p4)) & 0xFF

    def build_full_command(self, cmd_byte: int, p1: int, p2: int, p3: int, p4: int) -> bytes:
        checksum = self.calculate_checksum(cmd_byte, p1, p2, p3, p4)
        return struct.pack('BBBBBB', cmd_byte, p1, p2, p3, p4, checksum) + b'\r'

    def send_simple_command(self, command_char: str) -> Optional[bytes]:
        if command_char not in self.simple_commands_map:
            raise ValueError(f"Comando simples '{command_char}' não suportado")
        cmd_byte = self.simple_commands_map[command_char]
        cmd_packet = self.build_full_command(cmd_byte, 0xFF, 0xFF, 0xFF, 0xFF)

        if not self.connected or not self.serial:
            return None
        try:
            logger.debug(f"📤 Enviando comando '{command_char}': {cmd_packet.hex()}")
            self.serial.write(cmd_packet)
            time.sleep(0.2)
            response = self.serial.read(64)
            if response:
                logger.debug(f"📥 Resposta ({len(response)} bytes): {response.hex()}")
                return response
            else:
                logger.warning("❌ Sem resposta do SMS Gamer")
                return None
        except Exception as e:
            logger.error(f"❌ Erro ao enviar comando '{command_char}': {e}")
            return None


    def _interpret_q_response(self, response: bytes) -> Optional[Dict[str, Any]]:
        if not response or len(response) < 17:
            logger.warning(f"⚠️ Resposta muito curta ou vazia para interpretação: {len(response) if response else 0} bytes")
            return None

        try:
            if response[-1] == 0x0D:
                response = response[:-1]

            vin = struct.unpack(">I", response[1:5])[0] / 10.0
            vout = struct.unpack(">H", response[5:7])[0] / 10.0
            power = struct.unpack(">H", response[7:9])[0] / 10.0
            freq = struct.unpack(">H", response[9:11])[0] / 10.0
            batt = struct.unpack(">H", response[11:13])[0] / 10.0
            temp = struct.unpack(">H", response[13:15])[0] / 10.0
            extra = response[15]

            extra_flags_bin = f"{extra:08b}"

            flags_bits = {
                7: "BateriaEmUso",
                6: "BateriaBaixa",
                5: "ByPass",
                4: "Boost",
                3: "UpsOk",
                2: "TesteAtivo",
                1: "ShutdownAtivo",
                0: "BeepLigado",
            }

            flags_on = [name for bit, name in flags_bits.items() if extra & (1 << bit)]
            flags_str = ', '.join(flags_on) if flags_on else 'nenhuma flag ativa'

            data = {
                'vin': round(vin, 1),
                'vout': round(vout, 1),
                'load_percent': round(power, 1),
                'frequency': round(freq, 1),
                'battery_percent': round(batt, 1),
                'temperature': round(temp, 1),
                'extra_flags_raw': extra,
                'extra_flags_binary': extra_flags_bin,
                'active_flags': flags_on,
                'active_flags_str': flags_str,
                'raw_response_hex': response.hex(),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            return data

        except Exception as e:
            logger.error(f"❌ Erro ao interpretar pacote 'Q': {e}")
            return None

    def raw_monitor_loop(self, interval: float = 2):
        if not self.connected:
            logger.error("❌ Porta serial não conectada.")
            return

        logger.info(f"📡 Enviando 'Q' e lendo resposta a cada {interval:.1f}s...")
        try:
            while True:
                response = self.send_simple_command('Q')
                if response:
                    print(response.hex())
                    interpreted_data = self._interpret_q_response(response)
                    if interpreted_data:
                        render_status_humano(interpreted_data)
                else:
                    print("⚠️ (sem resposta ou resposta curta)")

                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("🛑 Interrompido pelo usuário.")

    def _on_mqtt_message(self, client, userdata, msg):
        """Callback para processar mensagens MQTT recebidas."""
        logger.info(f"📥 Mensagem MQTT recebida no tópico '{msg.topic}': {msg.payload.decode()}")
        try:
            payload = json.loads(msg.payload.decode())
            command_key = payload.get("command")

            if command_key:
                if command_key in SMS_GAMER_COMMANDS_PARAMS:
                    self.send_predefined_command(command_key)
                    logger.info(f"Comando '{command_key}' enviado via MQTT.")
                else:
                    logger.warning(f"Comando MQTT '{command_key}' não reconhecido ou não implementado para controle.")
            else:
                logger.warning("Payload MQTT de comando não contém 'command' key.")

        except json.JSONDecodeError:
            logger.error(f"❌ Erro ao decodificar payload JSON: {msg.payload.decode()}")
        except Exception as e:
            logger.error(f"❌ Erro ao processar comando MQTT: {e}")


    def connect_mqtt(self):
        try:
            self.mqtt_client = mqtt.Client(client_id=self.MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
            self.mqtt_client.username_pw_set(self.MQTT_USERNAME, self.MQTT_PASSWORD)
            self.mqtt_client.on_message = self._on_mqtt_message
            self.mqtt_client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            self.mqtt_client.subscribe(f"{self.MQTT_TOPIC_BASE}/command")
            logger.info(f"✅ Conectado ao broker MQTT em {self.MQTT_BROKER}:{self.MQTT_PORT} e assinando '{self.MQTT_TOPIC_BASE}/command'")

            # --- ROTINA PARA LIMPAR MENSAGENS DE COMANDO RETIDAS ---
            # Publica uma mensagem vazia com retain=True para limpar qualquer comando antigo retido.
            # Isso garante que comandos de reboot não sejam reexecutados.
            command_topic = f"{self.MQTT_TOPIC_BASE}/command"
            self.mqtt_client.publish(command_topic, payload=None, qos=1, retain=True)
            logger.info(f"✅ Limpando mensagens retidas no tópico de comando: '{command_topic}'")
            # --- FIM DA ROTINA ---

            return True
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao broker MQTT: {e}")
            return False

    def publish_discovery_messages(self):
        """Publica mensagens de descoberta MQTT para o Home Assistant."""
        if not self.mqtt_client:
            logger.error("❌ Cliente MQTT não conectado para publicar mensagens de descoberta.")
            return

        device_info = {
            "identifiers": [self.MQTT_CLIENT_ID],
            "name": self.DEVICE_NAME,
            "manufacturer": self.DEVICE_MANUFACTURER,
            "model": self.DEVICE_MODEL,
            "sw_version": self.DEVICE_SW_VERSION,
        }

        sensors_to_discover = {
            "vin": {"name": "Input Voltage", "unit_of_measurement": "V", "device_class": "voltage", "state_class": "measurement"},
            "vout": {"name": "Output Voltage", "unit_of_measurement": "V", "device_class": "voltage", "state_class": "measurement"},
            "load_percent": {"name": "Load Percent", "unit_of_measurement": "%", "icon": "mdi:gauge", "state_class": "measurement"},
            "frequency": {"name": "Frequency", "unit_of_measurement": "Hz", "device_class": "frequency", "state_class": "measurement"},
            "battery_percent": {"name": "Battery Percent", "unit_of_measurement": "%", "device_class": "battery", "state_class": "measurement"},
            "temperature": {"name": "Temperature", "unit_of_measurement": "°C", "device_class": "temperature", "state_class": "measurement"},
            "active_flags_str": {"name": "Active Flags", "icon": "mdi:information-outline"},
        }

        for key, config in sensors_to_discover.items():
            unique_id = f"{self.MQTT_CLIENT_ID}_{key}"
            config_topic = f"{self.HA_DISCOVERY_PREFIX}/sensor/{unique_id}/config"
            payload = {
                "name": f"{self.DEVICE_NAME} {config['name']}",
                "unique_id": unique_id,
                "state_topic": f"{self.MQTT_TOPIC_BASE}/status",
                "value_template": f"{{{{ value_json.{key} }}}}",
                "device": device_info,
                "qos": 1,
                "force_update": True
            }
            payload.update({k: v for k, v in config.items() if k != "name"})
            self.mqtt_client.publish(config_topic, json.dumps(payload), qos=1, retain=True)
            logger.info(f"✅ Publicado discovery para {config['name']} em {config_topic}")

        binary_flags = {
            "BateriaEmUso": {"name": "Battery In Use", "device_class": "running", "entity_category": "diagnostic"},
            "BateriaBaixa": {"name": "Low Battery", "device_class": "battery", "entity_category": "diagnostic"},
            "ByPass": {"name": "Bypass", "icon": "mdi:power-plug-off", "entity_category": "diagnostic"},
            "Boost": {"name": "Boost", "icon": "mdi:flash", "entity_category": "diagnostic"},
            "UpsOk": {"name": "UPS OK", "device_class": "problem", "entity_category": "diagnostic",
                      "value_template": "{% if 'UpsOk' in value_json.active_flags %}OFF{% else %}ON{% endif %}"},
            "TesteAtivo": {"name": "Test Active", "icon": "mdi:test-tube", "entity_category": "diagnostic"},
            "ShutdownAtivo": {"name": "Shutdown Active", "icon": "mdi:power-off", "entity_category": "diagnostic"},
            "BeepLigado": {"name": "Beep On", "icon": "mdi:volume-high", "entity_category": "diagnostic"},
        }

        for flag_key, config in binary_flags.items():
            unique_id = f"{self.MQTT_CLIENT_ID}_{flag_key.lower()}"
            config_topic = f"{self.HA_DISCOVERY_PREFIX}/binary_sensor/{unique_id}/config"
            payload = {
                "name": f"{self.DEVICE_NAME} {config['name']}",
                "unique_id": unique_id,
                "state_topic": f"{self.MQTT_TOPIC_BASE}/status",
                "device": device_info,
                "qos": 1,
                "retain": True
            }
            payload["value_template"] = config.get("value_template", f"{{% if '{flag_key}' in value_json.active_flags %}}ON{{% else %}}OFF{{% endif %}}")
            payload.update({k: v for k, v in config.items() if k not in ["name", "value_template"]})
            self.mqtt_client.publish(config_topic, json.dumps(payload), qos=1, retain=True)
            logger.info(f"✅ Publicado discovery para {config['name']} (Binary) em {config_topic}")

        # --- Controles (Switch e Button) ---
        beep_unique_id = f"{self.MQTT_CLIENT_ID}_beep_control"
        beep_config_topic = f"{self.HA_DISCOVERY_PREFIX}/switch/{beep_unique_id}/config"
        beep_payload = {
            "name": f"{self.DEVICE_NAME} Beep Control",
            "unique_id": beep_unique_id,
            "state_topic": f"{self.MQTT_TOPIC_BASE}/status",
            "value_template": "{% if 'BeepLigado' in value_json.active_flags %}ON{% else %}OFF{% endif %}",
            "command_topic": f"{self.MQTT_TOPIC_BASE}/command",
            "payload_on": '{"command": "M"}',
            "payload_off": '{"command": "M"}',
            "device": device_info,
            "qos": 1,
            "retain": True,
            "icon": "mdi:volume-high"
        }
        self.mqtt_client.publish(beep_config_topic, json.dumps(beep_payload), qos=1, retain=True)
        logger.info(f"✅ Publicado discovery para Beep Control em {beep_config_topic}")

        test_button_unique_id = f"{self.MQTT_CLIENT_ID}_battery_test"
        test_button_config_topic = f"{self.HA_DISCOVERY_PREFIX}/button/{test_button_unique_id}/config"
        test_button_payload = {
            "name": f"{self.DEVICE_NAME} Battery Test",
            "unique_id": test_button_unique_id,
            "command_topic": f"{self.MQTT_TOPIC_BASE}/command",
            "payload_press": '{"command": "T"}',
            "device": device_info,
            "qos": 1,
            "retain": True,
            "icon": "mdi:battery-charging"
        }
        self.mqtt_client.publish(test_button_config_topic, json.dumps(test_button_payload), qos=1, retain=True)
        logger.info(f"✅ Publicado discovery para Battery Test em {test_button_config_topic}")

        discharge_button_unique_id = f"{self.MQTT_CLIENT_ID}_battery_discharge"
        discharge_button_config_topic = f"{self.HA_DISCOVERY_PREFIX}/button/{discharge_button_unique_id}/config"
        discharge_button_payload = {
            "name": f"{self.DEVICE_NAME} Battery Discharge",
            "unique_id": discharge_button_unique_id,
            "command_topic": f"{self.MQTT_TOPIC_BASE}/command",
            "payload_press": '{"command": "D"}',
            "device": device_info,
            "qos": 1,
            "retain": True,
            "icon": "mdi:battery-alert"
        }
        self.mqtt_client.publish(discharge_button_config_topic, json.dumps(discharge_button_payload), qos=1, retain=True)
        logger.info(f"✅ Publicado discovery para Battery Discharge em {discharge_button_config_topic}")

        cancel_button_unique_id = f"{self.MQTT_CLIENT_ID}_cancel_action"
        cancel_button_config_topic = f"{self.HA_DISCOVERY_PREFIX}/button/{cancel_button_unique_id}/config"
        cancel_button_payload = {
            "name": f"{self.DEVICE_NAME} Cancel Action",
            "unique_id": cancel_button_unique_id,
            "command_topic": f"{self.MQTT_TOPIC_BASE}/command",
            "payload_press": '{"command": "C"}',
            "device": device_info,
            "qos": 1,
            "retain": True,
            "icon": "mdi:cancel"
        }
        self.mqtt_client.publish(cancel_button_config_topic, json.dumps(cancel_button_payload), qos=1, retain=True)
        logger.info(f"✅ Publicado discovery para Cancel Action em {cancel_button_config_topic}")

        shutdown_restore_button_unique_id = f"{self.MQTT_CLIENT_ID}_shutdown_restore"
        shutdown_restore_button_config_topic = f"{self.HA_DISCOVERY_PREFIX}/button/{shutdown_restore_button_unique_id}/config"
        shutdown_restore_button_payload = {
            "name": f"{self.DEVICE_NAME} Shutdown & Restore",
            "unique_id": shutdown_restore_button_unique_id,
            "command_topic": f"{self.MQTT_TOPIC_BASE}/command",
            "payload_press": '{"command": "R"}',
            "device": device_info,
            "qos": 1,
            "retain": True,
            "icon": "mdi:power-cycle"
        }
        self.mqtt_client.publish(shutdown_restore_button_config_topic, json.dumps(shutdown_restore_button_payload), qos=1, retain=True)
        logger.info(f"✅ Publicado discovery para Shutdown & Restore em {shutdown_restore_button_config_topic}")


    def mqtt_monitor_loop(self, interval: float): # interval agora é um parâmetro
        if not self.connected:
            logger.error("❌ Porta serial não conectada.")
            return
        if not self.mqtt_client and not self.connect_mqtt():
            logger.error("❌ Não foi possível conectar ao broker MQTT. Verifique as configurações.")
            return

        self.publish_discovery_messages()

        logger.info(f"📡 Monitorando e publicando dados no MQTT a cada {interval:.1f}s...")
        try:
            while True:
                response = self.send_simple_command('Q')
                if response:
                    interpreted_data = self._interpret_q_response(response)
                    if interpreted_data:
                        full_topic = f"{self.MQTT_TOPIC_BASE}/status"
                        payload = json.dumps(interpreted_data, ensure_ascii=False)
                        self.mqtt_client.publish(full_topic, payload, qos=1, retain=False)
                        logger.info(f"✅ Dados publicados no MQTT em '{full_topic}': {payload}")
                    else:
                        logger.warning("⚠️ Não foi possível interpretar a resposta do UPS.")
                else:
                    logger.warning("⚠️ Sem resposta do UPS para o comando 'Q'.")

                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("🛑 Interrompido pelo usuário.")
        except Exception as e:
            logger.error(f"❌ Erro no loop de monitoramento MQTT: {e}")


    def send_predefined_command(self, command_key: str) -> Optional[bytes]:
        params = SMS_GAMER_COMMANDS_PARAMS.get(command_key)
        if not params:
            logger.error(f"❌ Comando predefinido '{command_key}' não encontrado.")
            return None

        cmd_byte, p1, p2, p3, p4 = params
        cmd_packet = self.build_full_command(cmd_byte, p1, p2, p3, p4)

        if not self.connected or not self.serial:
            logger.error("❌ Porta serial não conectada para enviar comando predefinido.")
            return None

        try:
            logger.info(f"📤 Enviando comando predefinido '{command_key}': {cmd_packet.hex()}")
            self.serial.write(cmd_packet)
            time.sleep(1)
            response = self.serial.read(64)
            if response:
                logger.info(f"📥 Resposta ({len(response)} bytes): {response.hex()}")
                return response
            else:
                logger.warning(f"⚠️ Sem resposta para o comando predefinido '{command_key}'.")
                return None
        except Exception as e:
            logger.error(f"❌ Erro ao enviar comando predefinido '{command_key}': {e}")
            return None


def render_status_humano(data: Dict[str, Any]):
    print(f"  🔌 Vin: {data['vin']:.1f}V  ⚡ Vout: {data['vout']:.1f}V  🔋 Bat: {data['battery_percent']:.1f}%")
    print(f"  📊 Load: {data['load_percent']:.1f}%  🌡️ Temp: {data['temperature']:.1f}°C  📡 Freq: {data['frequency']:.1f}Hz")
    print(f"  🧩 Extra flags: 0b{data['extra_flags_binary']} → {data['active_flags_str']}")
    print(f"  ⏰ Timestamp: {data['timestamp']}")
    print("-" * 50)


def main():
    parser = argparse.ArgumentParser(description="SMS Gamer - Protocolo Real (v7)")
    # Argumentos que serão passados pelo run.sh do add-on
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Porta serial do UPS (ex: /dev/ttyUSB0)")
    parser.add_argument("--interval", type=int, default=10, help="Intervalo de polling em segundos")
    parser.add_argument("--mqtt-broker", default="core-mqtt", help="Endereço do broker MQTT (ex: core-mqtt)")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="Porta do broker MQTT")
    parser.add_argument("--mqtt-username", default="mqtt", help="Nome de usuário para autenticação MQTT")
    parser.add_argument("--mqtt-password", default="lna1001mqtt", help="Senha para autenticação MQTT")

    # Argumentos para uso local/debug (não usados pelo add-on em produção)
    parser.add_argument("--command", choices=['Q', 'I', 'F'], help="Comando a enviar (Q, I, F)")
    parser.add_argument("--json", action='store_true', help="Saída em formato JSON")
    parser.add_argument("--monitor", action='store_true', help="Monitoramento contínuo (saída no console)")
    parser.add_argument("--debug", action='store_true', help="Ativar debug detalhado")
    parser.add_argument("--raw", action='store_true', help="Monitoramento bruto + interpretado (saída no console)")
    parser.add_argument("--hex", help="Enviar comando hexadecimal manual (ex: '51 ff ff ff ff b3 0d')")
    parser.add_argument("--mqtt", action='store_true', help="Ativar modo de monitoramento e publicação MQTT (padrão para add-on)")
    parser.add_argument("--test-cmd", help=f"Envia um comando predefinido (ex: 'Q', 'I', 'D'). Opções: {', '.join(SMS_GAMER_COMMANDS_PARAMS.keys())}")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Instancia a classe do protocolo com as configurações lidas dos argumentos
    sms = SMSGamerProtocol(
        serial_port=args.port,
        mqtt_broker=args.mqtt_broker,
        mqtt_port=args.mqtt_port,
        mqtt_username=args.mqtt_username,
        mqtt_password=args.mqtt_password,
        mqtt_client_id=MQTT_CLIENT_ID, # Constante global
        mqtt_topic_base=MQTT_TOPIC_BASE, # Constante global
        ha_discovery_prefix=HA_DISCOVERY_PREFIX, # Constante global
        device_name=DEVICE_NAME, # Constante global
        device_manufacturer=DEVICE_MANUFACTURER, # Constante global
        device_model=DEVICE_MODEL, # Constante global
        device_sw_version=DEVICE_SW_VERSION # Constante global
    )

    try:
        # Lógica para os modos de operação (test-cmd, hex, raw, mqtt, monitor, default command)
        if args.test_cmd:
            if not sms.connect():
                sys.exit(1)
            try:
                response = sms.send_predefined_command(args.test_cmd)
                if response:
                    if args.test_cmd == 'Q':
                        interpreted_data = sms._interpret_q_response(response)
                        if interpreted_data:
                            print("\n--- Resposta Interpretada (Comando 'Q') ---")
                            render_status_humano(interpreted_data)
                        else:
                            print("\n--- Resposta Bruta (Comando 'Q') ---")
                            print(response.hex())
                    elif args.test_cmd == 'I':
                        try:
                            decoded_response = response.decode('ascii', errors='ignore').strip()
                            print(f"\n--- Resposta Interpretada (Comando 'I') ---")
                            print(f"Info: {decoded_response}")
                        except Exception as e:
                            print(f"\n--- Erro ao decodificar resposta 'I': {e} ---")
                            print(f"--- Resposta Bruta (Comando 'I') ---")
                            print(response.hex())
                else:
                    print(f"\n--- Resposta Bruta (Comando '{args.test_cmd}') ---")
                    print(response.hex())
            except Exception as e:
                logger.error(f"❌ Erro ao executar comando de teste '{args.test_cmd}': {e}")
            finally:
                sms.disconnect()
            return

        if args.hex:
            if not sms.connect():
                sys.exit(1)
            try:
                hex_bytes = bytes.fromhex(args.hex.replace(" ", ""))
                logger.info(f"📤 Enviando comando hexadecimal manual: {hex_bytes.hex()}")
                sms.serial.write(hex_bytes)
                time.sleep(1)
                resp = sms.serial.read(64)
                print(f"📤 Enviado: {hex_bytes.hex()}")
                print(f"📥 Resposta ({len(resp)} bytes): {resp.hex()}")
            except Exception as e:
                print(f"❌ Erro ao enviar comando hexadecimal: {e}")
            finally:
                sms.disconnect()
            return

        # O modo MQTT é o padrão para o add-on
        if args.mqtt:
            if not sms.connect():
                sys.exit(1)
            sms.mqtt_monitor_loop(interval=args.interval)
            return

        # Modos de monitoramento e comando para uso local (não usados pelo add-on)
        if not sms.connect():
            sys.exit(1)

        if args.raw:
            sms.raw_monitor_loop(interval=0.5)
            return

        if args.monitor:
            logger.info(f"🔄 Iniciando monitoramento (intervalo: {args.interval}s)")
            while True:
                data = sms._interpret_q_response(sms.send_simple_command('Q'))
                if data:
                    if args.json:
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                    else:
                        render_status_humano(data)
                time.sleep(args.interval)
        else: # Comando único (Q, I, F)
            if args.command == 'Q':
                data = sms._interpret_q_response(sms.send_simple_command('Q'))
            elif args.command == 'I':
                resp = sms.send_simple_command('I')
                data = {'info_response': resp.hex(), 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')} if resp else None
                if resp:
                    try:
                        data['decoded_info'] = resp.decode('ascii', errors='ignore').strip()
                    except Exception:
                        pass
            elif args.command == 'F':
                resp = sms.send_simple_command('F')
                data = {'features_response': resp.hex(), 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')} if resp else None
            else: # Default para 'Q' se nenhum comando for especificado e não for modo mqtt/monitor
                data = sms._interpret_q_response(sms.send_simple_command('Q'))


            if data:
                if args.json:
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                elif args.command == 'Q':
                    render_status_humano(data)
                elif args.command == 'I' and 'decoded_info' in data:
                    print(f"📋 Resposta (Comando 'I'):\n{data['decoded_info']}")
                else:
                    print(f"📋 Resposta:\n{data}")

    except KeyboardInterrupt:
        logger.info("⏹️ Interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        sys.exit(1)
    finally:
        sms.disconnect()


if __name__ == "__main__":
    main()
