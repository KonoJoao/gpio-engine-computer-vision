import os

import cv2 as cv
import paho.mqtt.client as mqtt

from DetectorMaos import DetectorMaos

# === Configuração do broker MQTT ===
MQTT_BROKER = os.getenv("MQTT_BROKER", "iot.coreflux.cloud")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "motor/velocidade")

cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cliente.connect(MQTT_BROKER, MQTT_PORT, 60)
print("Conectado ao broker MQTT")
cliente.loop_start()

camera = cv.VideoCapture(0)
rodando = True

detector = DetectorMaos(max_maos=1)

def calcular_velocidade(dedos_ativados):
    vel = 0

    if dedos_ativados != None:
        for ativado in dedos_ativados:
            if ativado:
                vel += 20

    return vel


while rodando:
    status, frame = camera.read()

    imagem = cv.flip(frame, 1)

    # --- Realizar a detecção das mãos --- #
    imagem, dedos_ativados = detector.encontrar_maos(imagem)

    vel = calcular_velocidade(dedos_ativados)

    # --- Publicar a velocidade atual no broker MQTT --- #
    if dedos_ativados != None:
        cliente.publish(MQTT_TOPIC, str(vel))
        print(f"Mensagem publicada no broker MQTT {str(vel)}")

    cv.putText(imagem, f'Velocidade atual: {str(vel)}%' if dedos_ativados != None else "Nenhuma mao detectada",
                   (100, 100), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # --- Lista com os pontos --- #
    lista_pontos = detector.encontrar_pontos(imagem)

    # --- Mostrar a imagem de captura --- #
    cv.imshow('Captura', imagem)

    if not status or cv.waitKey(1) & 0xff == ord('q'):
        rodando = False

cliente.loop_stop()
cliente.disconnect()
camera.release()
cv.destroyAllWindows()
