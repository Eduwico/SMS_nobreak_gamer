# SMS_nobreak_gamer
attempt to integrate an SMS nobreak to Home Assistant

# Home Assistant Custom Add-ons

🇧🇷 Repositório de add-ons personalizados para o Home Assistant OS, desenvolvidos para automação residencial local, monitoramento energético, comunicação com nobreaks inteligentes e controle avançado de rede.

🇺🇸 Custom Home Assistant OS add-ons designed for local automation, power monitoring, smart UPS communication, and advanced network control.

---

## 🧩 Add-ons incluídos / Included Add-ons

### 🔌 `sms-ups-monitor`
- 🇧🇷 Monitoramento e controle completo de nobreaks SMS (modelos Gamer 2000Bi/Bi, Lite, Net4+) via porta serial USB.
- Publicação de sensores e botões via MQTT Discovery para o Home Assistant.
- Interface em Python com interpretação de pacotes e fallback para comandos diretos.
- Uso zero de dependências externas além de `pyserial` e `paho-mqtt`.

- 🇺🇸 Full monitoring and control for SMS UPS devices (Gamer 2000Bi/Bi, Lite, Net4+) via USB serial.
- Publishes sensors and control buttons using MQTT Discovery for Home Assistant.
- Python-based interface with packet parsing and fallback to raw command mode.
- Minimal dependencies (`pyserial`, `paho-mqtt` only).

---


## 🧠 Requisitos / Requirements

- Home Assistant OS (Supervisor)
- Docker (já incluído no HAOS)
- Permissão para dispositivos seriais, se aplicável (ex: `/dev/ttyUSB0`)
- Broker MQTT configurado (local ou externo)

---

## 🙋 Suporte / Support

You're on your own. I'm  just trying to do a thing on my ups and thought it could bve useful to more people. Use some AI to try and modify for your use. This was done with manus.ai and chatGPT.
Se vira. Só fiz isso aqui pra testar meu nobreak e resolvi compartilhar. Use a inteligência artificial para mudar como quiser. Isso aqui foi feito com manus.ai e chatGPT.

Shout out to: https://github.com/dmslabsbr/smsUps 
