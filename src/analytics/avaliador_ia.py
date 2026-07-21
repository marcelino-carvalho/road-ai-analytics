# src/analysis/avaliador_ia.py


def avaliar_deteccao(ia_detectou, objeto_real):
    """
    Avalia se a IA detectou uma anomalia real.
    Não avalia se a classe está correta.
    """

    if not ia_detectou or not objeto_real:
        return "Sem dados"

    ia = ia_detectou.strip().lower()
    humano = objeto_real.strip().lower()

    # Ainda não avaliado
    if humano == "-":
        return "Pendente"

    # Humano descartou a detecção
    if humano == "desconhecido":
        return "Falso positivo"

    # IA conhece esses objetos
    if ia in (
        "buraco",
        "placa",
        "tampa_bueiro"
    ):
        return "Problema confirmado"

    return "Objeto IA não mapeado"


def avaliar_classificacao(ia_detectou, objeto_real):
    """
    Avalia se a classificação da IA bate com
    a classificação humana.
    """

    if not ia_detectou or not objeto_real:
        return "Sem dados"


    ia = ia_detectou.strip().lower()
    humano = objeto_real.strip().lower()



    # Ainda não avaliado
    if humano == "-":
        return "Pendente"



    # Falso positivo
    if humano == "desconhecido":
        return "Não aplicável"



    # ==========================
    # BURACO
    # ==========================

    if ia == "buraco":

        if humano == "pavimentação - buraco/panela":
            return "Classificação correta"

        elif humano.startswith("pavimentação"):
            return "Classe diferente"

        else:
            return "Classe diferente"



    # ==========================
    # PLACA
    # ==========================

    if ia == "placa":

        if humano.startswith("sinalização vertical"):
            return "Classificação correta"

        else:
            return "Classe diferente"



    # ==========================
    # TAMPA BUEIRO
    # ==========================

    if ia == "tampa_bueiro":

        if humano == "drenagem - poço de visita":
            return "Classificação correta"

        else:
            return "Classe diferente"



    return "Classe diferente"