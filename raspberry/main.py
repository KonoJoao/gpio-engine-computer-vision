import os
from time import sleep

import paho.mqtt.client as mqtt
from gpiozero import Servo
from gpiozero.pins.lgpio import LGPIOFactory

# === Configuração do broker MQTT ===
MQTT_BROKER = os.getenv("MQTT_BROKER", "iot.coreflux.cloud")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "motor/velocidade")

# === Configuração do ESC no GPIO18 ===
# factory = LGPIOFactory(chip=15)
factory = LGPIOFactory(chip=0)
brushless = Servo(18, min_pulse_width=1e-3, max_pulse_width=2e-3, pin_factory=factory)

# Inicializa motor no mínimo (parado)
brushless.value = -1
sleep(10)  # tempo para armar o ESC


# Função de mapeamento de velocidade (40% a 100%)
def map_speed(percent):
    percent = max(40, min(100, percent))  # limita faixa
    return -0.2 + (1.2 * (percent - 40) / 60)


# Velocidade atual publicada pela camada de visão computacional
velocidade_atual = 0


def ao_conectar(client, userdata, flags, reason_code, properties):
    client.subscribe(MQTT_TOPIC)


def ao_receber(client, userdata, msg):
    global velocidade_atual
    try:
        velocidade_atual = int(float(msg.payload.decode()))
        print(map_speed(velocidade_atual))
    except ValueError:
        return
    brushless.value = map_speed(velocidade_atual)


cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cliente.on_connect = ao_conectar
cliente.on_message = ao_receber
cliente.connect(MQTT_BROKER, MQTT_PORT, 60)

try:
    cliente.loop_forever()
except KeyboardInterrupt:
    pass
finally:
    brushless.value = -1
    cliente.disconnect()
