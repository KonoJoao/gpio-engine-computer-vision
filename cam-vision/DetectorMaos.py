import cv2 as cv
import mediapipe as mp

class DetectorMaos:
    """Classe responsável pela detecção das mãos."""

    """
    Função responsável por inicializar a classe.
    :param modo: Modo da captura da imagem. Se True, a detecção e rastreio serão feitos a todo momento;
    deixa muito travado. Se False, não são feitas a detecção e rastreio a todo momento; pode perder por
    alguns instântes as marcações, porém não trava.
    :param max_maos: Quantidade máxima de mãos para serem detectadas.
    :param deteccao_confianca: Percentual da taxa de detecção da mão. Se for menor do que este liminte,
    a detecção não ocorre.
    :param rastreio_confianca: Percentual da taxa de rastreio dos pontos da mão. Se for menor que este
    limite, o rastreio dos pontos não é realizado.
    :param cor_pontos: Cor dos pontos.
    :param cor_conexoes: Cor das conexões.
    """
    def __init__(self, modo=False, max_maos=2, deteccao_confianca=0.5,
                 rastreio_confianca=0.5, cor_pontos=(0, 0, 255), cor_conexoes=(255, 255, 255)):
        self.modo = modo
        self.max_maos = max_maos
        self.deteccao_confianca = deteccao_confianca
        self.rastreio_confianca = rastreio_confianca
        self.cor_pontos = cor_pontos
        self.cor_conexoes = cor_conexoes
        self.maos_mp = mp.solutions.hands

        self.maos = self.maos_mp.Hands(
            self.modo,
            self.max_maos,
            1,
            self.deteccao_confianca,
            self.rastreio_confianca
        )

        # --- Função para desenhar os pontos nas mãos --- #
        self.desenho_mp = mp.solutions.drawing_utils

        # --- Configurações do desenho dos pontos --- #
        self.desenho_config_pontos = self.desenho_mp.DrawingSpec(color=self.cor_pontos)

        # --- Configurações do desenho das conexões --- #
        self.desenho_config_conexoes = self.desenho_mp.DrawingSpec(color=self.cor_conexoes)

    def encontrar_maos(self, imagem, desenho=True):
            """
            Função responsável por detectar a(s) mão(s).
            :param imagem: Imagem capturada.
            :param desenho: Desenhar os pontos e as conexões na(s) mão(s).
            :return: Retorna a imagem com a detecção.
            """
            # --- Converter a imagem de BGR para RGB --- #
            imagem_rgb = cv.cvtColor(imagem, cv.COLOR_BGR2RGB)

            # --- Passar a imagem convertida para o detector --- #
            self.resultado = self.maos.process(imagem_rgb)

            h, w, _ = imagem.shape

            # --- Verificar se alguma mão foi detectada --- #
            pontos = []
            dedos = [8, 12, 16, 20]
            dedos_ativados = [False, False, False, False, False]

            if self.resultado.multi_hand_landmarks:
                for points in self.resultado.multi_hand_landmarks:
                    for id, cord in enumerate(points.landmark):
                        cx, cy = int(cord.x * w), int(cord.y * h)
                        cv.putText(imagem, str(id), (cx+10, cy+10), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                        pontos.append((cx, cy))
                        pass

                    if desenho:
                        # --- Desenhar os pontos nas mãos detectadas --- #
                        self.desenho_mp.draw_landmarks(
                            imagem,  # imagem de captura
                            points,  # pontos da mão
                            self.maos_mp.HAND_CONNECTIONS,  # conexão entre os pontos
                            self.desenho_config_pontos,  # cor dos pontos
                            self.desenho_config_conexoes  # cor das conexões
                        )


                for id, x in enumerate(dedos):
                    if id == 4:
                        continue

                    if pontos[x][1] < pontos[x-2][1]:
                          dedos_ativados[id] = True
                    elif pontos[x][1] > pontos[x - 2][1]:
                          dedos_ativados[id] = False

                    if pontos[4][0] > pontos[20][0]:
                        if pontos[4][0] > pontos[2][0]:
                            dedos_ativados[4] = True
                        elif pontos[4][0] < pontos[2][0]:
                            dedos_ativados[4] = False
                    else:
                        if pontos[4][0] < pontos[2][0]:
                            dedos_ativados[4] = True
                        elif pontos[4][0] > pontos[2][0]:
                            dedos_ativados[4] = False

            else:
                dedos_ativados = None

            return imagem, dedos_ativados

    def encontrar_pontos(self, imagem, mao_num=0, desenho=True, cor=(255, 0, 255), raio=7, ponto_detectado=0):
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
        # --- Lista com os pontos detectados --- #
        lista_pontos = []

        # --- Verificar se alguma mão foi detectada --- #
        if self.resultado.multi_hand_landmarks:
            # --- Obter os pontos da mão detectada, não de todas --- #
            mao = self.resultado.multi_hand_landmarks[mao_num]

            # --- Obter as informações dos pontos --- #
            for id, ponto in enumerate(mao.landmark):
                if id == ponto_detectado:
                    # --- Obter as dimenões da imagem capturada --- #
                    altura, largura, _ = imagem.shape

                    # --- Transformar a posição do ponto de proporção para pixel --- #
                    centro_x, centro_y = int(ponto.x * largura), int(ponto.y * altura)

                    # --- Adicionar os pontos da mão detectada na lista --- #
                    lista_pontos.append([id, centro_x, centro_y])

                    # --- Colocar um círculo em um ponto --- #
                    if desenho:
                        cv.circle(
                            imagem,  # imagem da captura
                            (centro_x, centro_y),  # centro do círculo
                            raio,  # raio do círculo
                            cor,  # cor do círculo
                            cv.FILLED  # espessura
                        )

        return lista_pontos

