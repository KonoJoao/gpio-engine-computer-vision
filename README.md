# gpio-engine-computer-vision

Projeto dividido em duas camadas que se comunicam via broker MQTT.

## Camadas

- **cam-vision**: roda em um notebook. Faz a visão computacional (detecção das mãos) e publica a velocidade atual no broker MQTT.
- **raspberry**: roda no Raspberry Pi. Consome a velocidade publicada no broker MQTT e ajusta a velocidade do motor brushless (ESC no GPIO18).

## Comunicação MQTT

- Tópico padrão: `motor/velocidade`
- Broker padrão: `localhost:1883`

Ambos podem ser configurados por variáveis de ambiente em cada camada:

| Variável      | Padrão              |
|---------------|---------------------|
| `MQTT_BROKER` | `localhost`         |
| `MQTT_PORT`   | `1883`              |
| `MQTT_TOPIC`  | `motor/velocidade`  |

## Execução

### cam-vision (notebook)

```bash
cd cam-vision
pip install -r requirements.txt
MQTT_BROKER=<ip-do-broker> python main.py
```

### raspberry

```bash
cd raspberry
pip install -r requirements.txt
MQTT_BROKER=<ip-do-broker> python main.py
```

O broker (ex.: Mosquitto) deve estar acessível por ambas as camadas.
