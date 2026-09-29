import cv2 as cv

from DetectorMaos import DetectorMaos
from gpiozero import Servo
from time import sleep
from gpiozero.pins.lgpio import LGPIOFactory
# factory = LGPIOFactory(chip=15)
factory = LGPIOFactory(chip=0)

camera = cv.VideoCapture(0)
rodando = True

detector = DetectorMaos(max_maos=1)

# === Configuração do ESC no GPIO18 ===
brushless = Servo(18, min_pulse_width=1e-3, max_pulse_width=2e-3, pin_factory=factory)

# Inicializa motor no mínimo (parado)
brushless.value = -1
sleep(10)  # tempo para armar o ESC

# Função de mapeamento de velocidade (40% a 100%)
def map_speed(percent):
    percent = max(40, min(100, percent))  # limita faixa
    return -0.2 + (1.2 * (percent - 40) / 60)

while rodando:
    status, frame = camera.read()

    imagem = cv.flip(frame, 1)

    # --- Realizar a detecção das mãos --- #
    imagem, vel = detector.encontrar_maos(imagem)

    cv.putText(imagem, f'Velocidade atual: {str(vel)}%', (100, 100), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    brushless.value = map_speed(vel)

    # --- Lista com os pontos --- #
    lista_pontos = detector.encontrar_pontos(imagem)

    # --- Mostrar a imagem de captura --- #
    cv.imshow('Captura', imagem)

    if not status or cv.waitKey(1) & 0xff == ord('q'):
        rodando = False