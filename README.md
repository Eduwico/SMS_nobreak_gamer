# Repositório de Add-ons para Home Assistant - SMS Gamer UPS Monitor

Este repositório contém o add-on personalizado para Home Assistant que permite monitorar e controlar nobreaks SMS Gamer via comunicação serial e integração MQTT.

---

## ⚠️ ALERTA: PROJETO EXPERIMENTAL E EM DESENVOLVIMENTO ⚠️

**Este add-on está em fase de desenvolvimento inicial e é considerado experimental.**

*   **Não é garantido que seja totalmente funcional ou estável.**
*   **Pode conter bugs e comportamentos inesperados.**
*   **O uso é por sua conta e risco.**
*   **Ainda não foram realizados testes extensivos em diferentes modelos de nobreaks SMS Gamer ou em todas as funcionalidades.**

**Recomenda-se cautela ao utilizá-lo em ambientes de produção. Contribuições e feedback são bem-vindos para ajudar a estabilizar e melhorar o projeto.**

---

## Visão Geral

O add-on "SMS Gamer UPS Monitor" integra seu nobreak SMS Gamer ao Home Assistant, fornecendo:
*   Monitoramento de status (tensão de entrada/saída, carga, bateria, temperatura, frequência).
*   Detecção de flags de status (bateria em uso, bateria baixa, bypass, etc.).
*   Controle de comandos (ligar/desligar beep, iniciar teste de bateria, descarga, desligamento programado) via entidades de botão e switch no Home Assistant.
*   Utiliza MQTT Discovery para configuração automática no Home Assistant.

## Instalação (Para Usuários Avançados)

Este add-on é um repositório personalizado. Para adicioná-lo ao seu Home Assistant:

1.  No Home Assistant, vá para **Configurações** (Settings) -> **Add-ons**.
2.  Clique nos **três pontos verticais** no canto inferior direito (ao lado de "Loja de Add-ons").
3.  Selecione **Repositórios** (Repositories).
4.  No campo "Adicionar", cole a URL deste repositório:
    `https://github.com/YOUR_GITHUB_USERNAME/your-addon-repository.git`
    *(Lembre-se de substituir `YOUR_GITHUB_USERNAME` pelo seu nome de usuário real do GitHub. )*
5.  Clique em **Adicionar**.
6.  Feche a janela de repositórios.
7.  Na página "Add-ons", clique em **Atualizar** (Refresh) no canto inferior direito.
8.  O novo repositório "SMS Gamer UPS Monitor" deverá aparecer na lista da Loja de Add-ons.

### Instalação do Add-on

1.  Clique no add-on "SMS Gamer UPS Monitor" na Loja de Add-ons.
2.  Clique em **Instalar**.
3.  Após a instalação, vá para a aba **Configuração**.
4.  Ajuste as opções conforme sua necessidade:
    *   `serial_port`: A porta serial onde seu nobreak está conectado (ex: `/dev/ttyUSB0`).
    *   `poll_interval`: Intervalo de tempo (em segundos) entre as leituras do nobreak.
    *   `mqtt_broker`: Endereço do seu broker MQTT (se estiver usando o add-on oficial do Mosquitto, use `core-mqtt`).
    *   `mqtt_port`: Porta do seu broker MQTT (geralmente `1883`).
    *   `mqtt_username`: Nome de usuário para autenticação no broker MQTT.
    *   `mqtt_password`: Senha para autenticação no broker MQTT.
5.  Clique em **Salvar**.
6.  Na aba **Informações**, ative a opção **Iniciar na inicialização** (Start on boot).
7.  Clique em **Iniciar**.

### Verificando o Status

Você pode verificar o status e os logs do add-on na aba **Logs** da página do add-on. Procure por mensagens indicando a conexão com a porta serial, o broker MQTT e a publicação de dados.

Após alguns segundos, as entidades do seu nobreak (sensores, binários, botões) deverão aparecer automaticamente no Home Assistant via MQTT Discovery. Você pode encontrá-las em **Ferramentas do Desenvolvedor** -> **Estados** ou na lista de entidades.

## Contribuição

Contribuições são bem-vindas! Se você encontrar um bug, tiver uma sugestão de melhoria ou quiser adicionar suporte a outros modelos de nobreak SMS Gamer, sinta-se à vontade para abrir uma issue ou enviar um pull request.

## Licença

Este projeto está licenciado sob a **GNU General Public License v3.0**. Veja o arquivo `LICENSE` para mais detalhes.
