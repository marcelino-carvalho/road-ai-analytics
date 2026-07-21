familias = {

    "Pavimentação": [

        "Pavimentação - Buraco/Panela",
        "Pavimentação - Desgaste",
        "Pavimentação - Escorregamento",
        "Pavimentação - Remendo",
        "Pavimentação - Trincas Interligadas Tipo Couro de Jacaré",
        "Pavimentação - Trincas Isoladas Longitudinais",
        "Pavimentação - Trincas Isoladas Transversais"

    ],


    "Drenagem": [

        "Drenagem - Poço de Visita",
        "Drenagem - Boca de Lobo"

    ],


    "Sinalização Vertical": [

        "Sinalização Vertical - Placa Coberta Vegetação",
        "Sinalização Vertical - Placa com Avaria",
        "Sinalização Vertical - Placa Pixada",
        "Sinalização Vertical - Placa Suja"

    ],


    "Sinalização Horizontal": [

        "Sinalização Horizontal – Pintura Faixa Desgastada",
        "Sinalização Horizontal – Pintura Faixa Faltando",
        "Sinalização Horizontal – Tacha Faltando"

    ]

}

def identificar_familia(objeto_real):

    for familia, problemas in familias.items():

        if objeto_real in problemas:

            return familia


    if objeto_real == "Desconhecido":
        return "Sem problema"


    if objeto_real == "-":
        return "Pendente"


    return "Não identificado"