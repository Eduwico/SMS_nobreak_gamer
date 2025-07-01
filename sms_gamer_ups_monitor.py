#!/usr/bin/env python3


"""
Script SMS Gamer - Protocolo Real (v7) - Versão Melhorada
Serviço de monitoramento para Home Assistant via MQTT com MQTT Discovery e controle de comandos.

Melhorias implementadas:
- Constantes globais para informações do dispositivo
- Parâmetros configuráveis (baud_rate, timeout)
- Tratamento robusto de reconexão MQTT
- Documentação completa com docstrings
- Type hints para melhor legibilidade
- Novos comandos adicionados (comentados para referência)
- Remoção de credenciais hardcoded
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

# Configurações para MQTT Discovery (constantes globais)
HA_DISCOVERY_PREFIX = "homeassistant"
MQTT_CLIENT_ID = "sms_gamer_monitor"  # ID único para o cliente MQTT
MQTT_TOPIC_BASE = "sms_gamer/ups"     # Tópico base para status e comandos

DEVICE_NAME = "SMS Gamer UPS"
DEVICE_MANUFACTURER = "SMS"
DEVICE_MODEL = "Gamer"
DEVICE_SW_VERSION = "v7"  # Versão do script/firmware do UPS

# Configurações padrão para porta serial (configuráveis via argumentos)
BAUD_RATE = 2400  # Padrão para SMS Gamer, mas configurável
TIMEOUT = 3       # Timeout padrão em segundos

# Comandos predefinidos com seus parâmetros (cmd_byte, p1, p2, p3, p4)
SMS_GAMER_COMMANDS_PARAMS = {
    # Comandos básicos de consulta
    'Q': (0x51, 0xFF, 0xFF, 0xFF, 0xFF),  # Status geral do UPS
    'I': (0x49, 0xFF, 0xFF, 0xFF, 0xFF),  # Informações do dispositivo
    'F': (0x46, 0xFF, 0xFF, 0xFF, 0xFF),  # Features/características
    
    # Comandos de controle
    'M': (0x4D, 0xFF, 0xFF, 0xFF, 0xFF),  # Toggle beep (liga/desliga)
    'D': (0x44, 0xFF, 0xFF, 0xFF, 0xFF),  # Descarga da bateria (teste)
    'C': (0x43, 0xFF, 0xFF, 0xFF, 0xFF),  # Cancelar operação ativa
    'G': (0x47, 0x01, 0xFF, 0xFF, 0xFF),  # Comando G (função específica)
    'L': (0x4C, 0xFF, 0xFF, 0xFF, 0xFF),  # Comando L (função específica)
    
    # Comandos de teste de bateria (diferentes durações)
    'T': (0x54, 0x00, 0x10, 0x00, 0x00),   # Teste rápido (16 segundos)
    'T1': (0x54, 0x00, 0x64, 0x00, 0x00),  # Teste 100 segundos
    'T2': (0x54, 0x00, 0xC8, 0x00, 0x00),  # Teste 200 segundos
    'T3': (0x54, 0x01, 0x2C, 0x00, 0x00),  # Teste 300 segundos
    'T9': (0x54, 0x03, 0x84, 0x00, 0x00),  # Teste 900 segundos
    
    # Comandos de shutdown/restart (CUIDADO: podem desligar o UPS!)
    'R': (0x52, 0x00, 0xC8, 0x27, 0x0F),   # Shutdown & Restore
    # "zzz": (0x52, 0x00, 0xC8, 0x0F, 0xEF),  # Comando experimental (comentado)
    # "zz1": (0x52, 0x01, 0x2C, 0x27, 0x0F),  # Comando experimental (comentado)
    
    # Novos comandos descobertos (comentados para segurança - descomente com cuidado)
    # 'S': (0x53, 0xFF, 0xFF, 0xFF, 0xFF),    # Shutdown imediato (PERIGOSO!)
    # 'N': (0x4E, 0xFF, 0xFF, 0xFF, 0xFF),    # Comando N (função desconhecida)
    # 'P': (0x50, 0xFF, 0xFF, 0xFF, 0xFF),    # Comando P (função desconhecida)
    # 'U': (0x55, 0xFF, 0xFF, 0xFF, 0xFF),    # Comando U (função desconhecida)
    # 'W': (0x57, 0xFF, 0xFF, 0xFF, 0xFF),    # Comando W (função desconhecida)
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
    """
    Gerencia a comunicação com o nobreak SMS Gamer via porta serial
    e integra com Home Assistant via MQTT.
    
    Esta classe implementa o protocolo de comunicação específico do SMS Gamer,
    incluindo descoberta automática para Home Assistant e controle via MQTT.
    """
    
    def __init__(self, serial_port: str, mqtt_broker: str, mqtt_port: int, 
                 mqtt_username: str, mqtt_password: str, baud_rate: int = BAUD_RATE, 
                 timeout: int = TIMEOUT):
        """
        Inicializa a classe SMSGamerProtocol.

        Args:
            serial_port (str): Caminho para a porta serial (ex: '/dev/ttyUSB0').
            mqtt_broker (str): Endereço IP ou hostname do broker MQTT.
            mqtt_port (int): Porta do broker MQTT.
            mqtt_username (str): Nome de usuário para autenticação MQTT.
            mqtt_password (str): Senha para autenticação MQTT.
            baud_rate (int): Baudrate da comunicação serial (padrão: 2400).
            timeout (int): Timeout da comunicação serial em segundos (padrão: 3).
        """
        self.port = serial_port
        self.serial = None
        self.connected = False
        self.baud_rate = baud_rate
        self.timeout = timeout
        
        # Mapeamento de comandos simples para compatibilidade
        self.simple_commands_map = {
            'Q': 0x51,
            'I': 0x49,
            'F': 0x46,
        }
        
        self.mqtt_client = None

        # Configurações MQTT e Discovery (usando constantes globais)
        self.MQTT_BROKER = mqtt_broker
        self.MQTT_PORT = mqtt_port
        self.MQTT_USERNAME = mqtt_username
        self.MQTT_PASSWORD = mqtt_password
        self.MQTT_CLIENT_ID = MQTT_CLIENT_ID
        self.MQTT_TOPIC_BASE = MQTT_TOPIC_BASE
        self.HA_DISCOVERY_PREFIX = HA_DISCOVERY_PREFIX
        self.DEVICE_NAME = DEVICE_NAME
        self.DEVICE_MANUFACTURER = DEVICE_MANUFACTURER
        self.DEVICE_MODEL = DEVICE_MODEL
        self.DEVICE_SW_VERSION = DEVICE_SW_VERSION

    def connect(self) -> bool:
        """
        Tenta estabelecer uma conexão com a porta serial do nobreak.

        Returns:
            bool: True se a conexão for bem-sucedida, False caso contrário.
        """
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )
            self.connected = True
            logger.info(f"✅ Conectado ao SMS Gamer em {self.port} (Baud: {self.baud_rate}, Timeout: {self.timeout}s)")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {e}")
            return False

    def disconnect(self):
        """
        Desconecta da porta serial e do broker MQTT de forma limpa.
        """
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.connected = False
            logger.info("🔌 Desconectado do SMS Gamer")
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            self.mqtt_client.loop_stop()
            logger.info("🔌 Desconectado do broker MQTT")

    def calculate_checksum(self, cmd_byte: int, p1: int, p2: int, p3: int, p4: int) -> int:
        """
        Calcula o checksum para um comando do protocolo SMS Gamer.

        Args:
            cmd_byte (int): Byte do comando.
            p1, p2, p3, p4 (int): Parâmetros do comando.

        Returns:
            int: Checksum calculado.
        """
        return (-1 * (cmd_byte + p1 + p2 + p3 + p4)) & 0xFF

    def build_full_command(self, cmd_byte: int, p1: int, p2: int, p3: int, p4: int) -> bytes:
        """
        Constrói um comando completo do protocolo SMS Gamer.

        Args:
            cmd_byte (int): Byte do comando.
            p1, p2, p3, p4 (int): Parâmetros do comando.

        Returns:
            bytes: Comando completo pronto para envio.
        """
        checksum = self.calculate_checksum(cmd_byte, p1, p2, p3, p4)
        return struct.pack('BBBBBB', cmd_byte, p1, p2, p3, p4, checksum) + b'\r'

    def send_simple_command(self, command_char: str) -> Optional[bytes]:
        """
        Envia um comando simples (Q, I, F) para o UPS.

        Args:
            command_char (str): Caractere do comando ('Q', 'I', ou 'F').

        Returns:
            Optional[bytes]: Resposta do UPS ou None se houver erro.
        """
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
        """
        Interpreta a resposta do comando 'Q' (status do UPS).

        Args:
            response (bytes): Resposta bruta do UPS.

        Returns:
            Optional[Dict[str, Any]]: Dados interpretados ou None se houver erro.
        """
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

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """
        Callback executado quando o cliente MQTT se conecta ou reconecta ao broker.
        Assina tópicos, limpa mensagens retidas e publica discovery.
        """
        if rc == 0:
            logger.info("✅ Conectado ao broker MQTT com sucesso.")
            # Assina o tópico de comando novamente em caso de reconexão
            client.subscribe(f"{self.MQTT_TOPIC_BASE}/command")
            logger.info(f"✅ Assinado '{self.MQTT_TOPIC_BASE}/command' após reconexão.")
            # Limpa mensagens retidas após reconexão
            command_topic = f"{self.MQTT_TOPIC_BASE}/command"
            client.publish(command_topic, payload=None, qos=1, retain=True)
            logger.info(f"✅ Limpando mensagens retidas no tópico de comando: '{command_topic}' após reconexão.")
            # Publica mensagens de discovery novamente em caso de reconexão
            self.publish_discovery_messages()
        else:
            logger.error(f"❌ Falha na conexão MQTT, código de retorno: {rc}")

    def _on_mqtt_disconnect(self, client, userdata, rc):
        """
        Callback executado quando o cliente MQTT se desconecta do broker.
        """
        if rc != 0:
            logger.warning(f"⚠️ Desconexão inesperada do broker MQTT. Tentando reconectar... (código: {rc})")
        else:
            logger.info("🔌 Desconectado do broker MQTT.")

    def _on_mqtt_message(self, client, userdata, msg):
        """
        Callback para processar mensagens MQTT recebidas.
        
        Args:
            client: Cliente MQTT.
            userdata: Dados do usuário.
            msg: Mensagem MQTT recebida.
        """
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
        """
        Conecta ao broker MQTT com tratamento robusto de reconexão.

        Returns:
            bool: True se a conexão for bem-sucedida, False caso contrário.
        """
        try:
            self.mqtt_client = mqtt.Client(client_id=self.MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
            self.mqtt_client.username_pw_set(self.MQTT_USERNAME, self.MQTT_PASSWORD)
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
            self.mqtt_client.on_message = self._on_mqtt_message

            # Configura a reconexão automática
            self.mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)

            self.mqtt_client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.mqtt_client.loop_start()  # Inicia o loop em uma thread separada

            logger.info(f"✅ Tentando conectar ao broker MQTT em {self.MQTT_BROKER}:{self.MQTT_PORT}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao broker MQTT: {e}")
            return False

    def publish_discovery_messages(self):
        """
        Publica mensagens de descoberta MQTT para o Home Assistant.
        Cria sensores, binary sensors, switches e buttons automaticamente.
        """
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

        # Sensores numéricos
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

        # Binary sensors (flags de status)
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

        # Controles (Switch para beep)
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

        # Buttons para ações
        buttons_config = {
            "battery_test": {"name": "Battery Test", "command": "T", "icon": "mdi:battery-charging"},
            "battery_discharge": {"name": "Battery Discharge", "command": "D", "icon": "mdi:battery-alert"},
            "cancel_action": {"name": "Cancel Action", "command": "C", "icon": "mdi:cancel"},
            "shutdown_restore": {"name": "Shutdown & Restore", "command": "R", "icon": "mdi:power-cycle"},
        }

        for button_key, config in buttons_config.items():
            unique_id = f"{self.MQTT_CLIENT_ID}_{button_key}"
            config_topic = f"{self.HA_DISCOVERY_PREFIX}/button/{unique_id}/config"
            payload = {
                "name": f"{self.DEVICE_NAME} {config['name']}",
                "unique_id": unique_id,
                "command_topic": f"{self.MQTT_TOPIC_BASE}/command",
                "payload_press": f'{{"command": "{config["command"]}"}}',
                "device": device_info,
                "qos": 1,
                "retain": True,
                "icon": config["icon"]
            }
            self.mqtt_client.publish(config_topic, json.dumps(payload), qos=1, retain=True)
            logger.info(f"✅ Publicado discovery para {config['name']} em {config_topic}")

    def mqtt_monitor_loop(self, interval: float = 10):
        """
        Loop principal de monitoramento MQTT.

        Args:
            interval (float): Intervalo entre leituras em segundos.
        """
        if not self.connected:
            logger.error("❌ Porta serial não conectada.")
            return
        if not self.mqtt_client and not self.connect_mqtt():
            logger.error("❌ Não foi possível conectar ao broker MQTT. Verifique as configurações.")
            return

        # Aguarda um pouco para garantir que a conexão MQTT esteja estabelecida
        time.sleep(2)

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
                        logger.info(f"✅ Dados publicados no MQTT em '{full_topic}'")
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
        """
        Envia um comando predefinido para o UPS.

        Args:
            command_key (str): Chave do comando no dicionário SMS_GAMER_COMMANDS_PARAMS.

        Returns:
            Optional[bytes]: Resposta do UPS ou None se houver erro.
        """
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


def main():
    """
    Função principal do script.
    """
    parser = argparse.ArgumentParser(
        description="SMS Gamer - Protocolo Real (v7) - Versão Melhorada",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--port", help="Porta serial")
    parser.add_argument("--interval", type=int, help="Intervalo entre leituras (s)")
    parser.add_argument("--baud-rate", type=int, default=BAUD_RATE, help="Baudrate da porta serial")
    parser.add_argument("--timeout", type=int, default=TIMEOUT, help="Timeout da porta serial em segundos")
    parser.add_argument("--mqtt-broker", help="Endereço do broker MQTT")
    parser.add_argument("--mqtt-port", type=int, help="Porta do broker MQTT")
    parser.add_argument("--mqtt-username", help="Nome de usuário para autenticação MQTT")
    parser.add_argument("--mqtt-password", help="Senha para autenticação MQTT")
    parser.add_argument("--mqtt", action='store_true', help="Monitoramento e publicação via MQTT (modo serviço)")
    parser.add_argument("--test-cmd", help=f"Envia um comando predefinido. Opções: {', '.join(SMS_GAMER_COMMANDS_PARAMS.keys())}")

    args = parser.parse_args()

    # Instancia a classe do protocolo com as configurações lidas dos argumentos
    sms = SMSGamerProtocol(
        serial_port=args.port,
        mqtt_broker=args.mqtt_broker,
        mqtt_port=args.mqtt_port,
        mqtt_username=args.mqtt_username,
        mqtt_password=args.mqtt_password,
        baud_rate=args.baud_rate,
        timeout=args.timeout
    )

    try:
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
                            print(json.dumps(interpreted_data, indent=2, ensure_ascii=False))
                        else:
                            print("\n--- Resposta Bruta (Comando 'Q') ---")
                            print(response.hex())
                    else:
                        print(f"\n--- Resposta Bruta (Comando '{args.test_cmd}') ---")
                        print(response.hex())
            except Exception as e:
                logger.error(f"❌ Erro ao executar comando de teste '{args.test_cmd}': {e}")
            finally:
                sms.disconnect()
            return

        if not sms.connect():
            sys.exit(1)

        if args.mqtt:
            sms.mqtt_monitor_loop(interval=args.interval)
            return

    except KeyboardInterrupt:
        logger.info("⏹️ Interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        sys.exit(1)
    finally:
        sms.disconnect()


if __name__ == "__main__":
    main()
