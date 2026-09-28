import cv2 as cv

from DetectorMaos import DetectorMaos

camera = cv.VideoCapture(0)
rodando = True

detector = DetectorMaos(max_maos=1)

while rodando:
    status, frame = camera.read()

    imagem = cv.flip(frame, 1)

    # --- Realizar a detecção das mãos --- #
    imagem, vel = detector.encontrar_maos(imagem)

    cv.putText(imagem, f'Velocidade atual: {str(vel)}%', (100, 100), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # --- Lista com os pontos --- #
    lista_pontos = detector.encontrar_pontos(imagem)

    # --- Mostrar a imagem de captura --- #
    cv.imshow('Captura', imagem)

    if not status or cv.waitKey(1) & 0xff == ord('q'):
        rodando = False

