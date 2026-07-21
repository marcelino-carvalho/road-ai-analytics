from src.analytics.avaliador_ia import (
    avaliar_deteccao,
    avaliar_classificacao
)


resultado1 = avaliar_deteccao(
    "Buraco",
    "Pavimentação - Afundamento"
)

resultado2 = avaliar_classificacao(
    "Buraco",
    "Pavimentação - Afundamento"
)


print(resultado1)
print(resultado2)