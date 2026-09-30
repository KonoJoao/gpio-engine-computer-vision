import time
import cv2 as cv
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision


class DetectorMaos:
    """Classe responsável pela detecção das mãos."""

    # Conexões entre os 21 pontos da mão (equivalente ao antigo HAND_CONNECTIONS)
    CONEXOES_MAO = [
        (0, 1), (1, 2), (2, 3), (3, 4),          # polegar
        (0, 5), (5, 6), (6, 7), (7, 8),          # indicador
        (5, 9), (9, 10), (10, 11), (11, 12),     # médio
        (9, 13), (13, 14), (14, 15), (15, 16),   # anelar
        (13, 17), (17, 18), (18, 19), (19, 20),  # mínimo
        (0, 17),                                 # palma
    ]

    def __init__(self, modo=False, max_maos=2, deteccao_confianca=0.5,
                 rastreio_confianca=0.5, cor_pontos=(0, 0, 255), cor_conexoes=(255, 255, 255),
                 caminho_modelo="hand_landmarker.task"):
        """
        :param modo: Se True, a detecção é feita a cada frame (IMAGE); mais pesado.
        Se False, usa detecção + rastreio (VIDEO); mais leve.
        :param max_maos: Quantidade máxima de mãos para serem detectadas.
        :param deteccao_confianca: Confiança mínima para detectar a mão.
        :param rastreio_confianca: Confiança mínima para o rastreio dos pontos.
        :param cor_pontos: Cor dos pontos (BGR).
        :param cor_conexoes: Cor das conexões (BGR).
        :param caminho_modelo: Caminho do arquivo hand_landmarker.task.
        """
        self.modo = modo
        self.max_maos = max_maos
        self.deteccao_confianca = deteccao_confianca
        self.rastreio_confianca = rastreio_confianca
        self.cor_pontos = cor_pontos
        self.cor_conexoes = cor_conexoes
        self.resultado = None
        self._inicio = time.monotonic()
        self._ultimo_timestamp = -1

        self.running_mode = (vision.RunningMode.IMAGE if self.modo
                             else vision.RunningMode.VIDEO)

        opcoes = vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=caminho_modelo),
            running_mode=self.running_mode,
            num_hands=self.max_maos,
            min_hand_detection_confidence=self.deteccao_confianca,
            min_hand_presence_confidence=self.deteccao_confianca,
            min_tracking_confidence=self.rastreio_confianca,
        )
        self.maos = vision.HandLandmarker.create_from_options(opcoes)

    def _timestamp_ms(self):
        """Timestamp crescente em ms (exigido pelo modo VIDEO)."""
        ts = int((time.monotonic() - self._inicio) * 1000)
        if ts <= self._ultimo_timestamp:
            ts = self._ultimo_timestamp + 1
        self._ultimo_timestamp = ts
        return ts

    def _desenhar_mao(self, imagem, landmarks):
        """Substitui o antigo drawing_utils.draw_landmarks."""
        h, w, _ = imagem.shape
        pts = [(int(p.x * w), int(p.y * h)) for p in landmarks]

        for a, b in self.CONEXOES_MAO:
            cv.line(imagem, pts[a], pts[b], self.cor_conexoes, 2)
        for p in pts:
            cv.circle(imagem, p, 4, self.cor_pontos, cv.FILLED)

    def encontrar_maos(self, imagem, desenho=True):
        """
        Função responsável por detectar a(s) mão(s).
        :param imagem: Imagem capturada.
        :param desenho: Desenhar os pontos e as conexões na(s) mão(s).
        :return: Retorna a imagem com a detecção e a velocidade calculada.
        """
        # --- Converter a imagem de BGR para RGB e criar o mp.Image --- #
        imagem_rgb = cv.cvtColor(imagem, cv.COLOR_BGR2RGB)
        mp_imagem = mp.Image(image_format=mp.ImageFormat.SRGB, data=imagem_rgb)

        # --- Passar a imagem para o detector --- #
        if self.running_mode == vision.RunningMode.VIDEO:
            self.resultado = self.maos.detect_for_video(mp_imagem, self._timestamp_ms())
        else:
            self.resultado = self.maos.detect(mp_imagem)

        h, w, _ = imagem.shape

        pontos = []
        vel = 0
        dedos = [8, 12, 16, 20]
        dedos_ativados = [False, False, False, False, False]

        maos_detectadas = self.resultado.hand_landmarks

        if maos_detectadas:
            for landmarks in maos_detectadas:
                for id, cord in enumerate(landmarks):
                    cx, cy = int(cord.x * w), int(cord.y * h)
                    cv.putText(imagem, str(id), (cx + 10, cy + 10),
                               cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    pontos.append((cx, cy))

                if desenho:
                    self._desenhar_mao(imagem, landmarks)

            for id, x in enumerate(dedos):
                if pontos[x][1] < pontos[x - 2][1]:
                    dedos_ativados[id] = True
                elif pontos[x][1] > pontos[x - 2][1]:
                    dedos_ativados[id] = False

            if pontos[4][0] < pontos[2][0]:
                dedos_ativados[4] = True
            elif pontos[4][0] > pontos[2][0]:
                dedos_ativados[4] = False

            for ativado in dedos_ativados:
                if ativado:
                    vel += 20

        return imagem, vel

    def encontrar_pontos(self, imagem, mao_num=0, desenho=True, cor=(255, 0, 255),
                         raio=7, ponto_detectado=0):
        """
        Função responsável por encontrar a posição dos pontos da(s) mão(s).
        :param imagem: Imagem capturada.
        :param mao_num: Número da mão detectada.
        :param desenho: Desenhar o ponto encontrado.
        :param cor: Tupla com a cor do ponto (BGR).
        :param raio: Raio do círculo do ponto.
        :param ponto_detectado: Ponto a ser detectado.
        :return: Lista com os pontos detectados.
        """
        lista_pontos = []

        if self.resultado and self.resultado.hand_landmarks:
            if mao_num >= len(self.resultado.hand_landmarks):
                return lista_pontos

            mao = self.resultado.hand_landmarks[mao_num]
            altura, largura, _ = imagem.shape

            for id, ponto in enumerate(mao):
                if id == ponto_detectado:
                    centro_x, centro_y = int(ponto.x * largura), int(ponto.y * altura)
                    lista_pontos.append([id, centro_x, centro_y])

                    if desenho:
                        cv.circle(imagem, (centro_x, centro_y), raio, cor, cv.FILLED)

        return lista_pontos

    def fechar(self):
        """Libera os recursos do detector."""
        self.maos.close()