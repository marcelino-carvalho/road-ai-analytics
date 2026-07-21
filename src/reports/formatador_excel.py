import os
import openpyxl

from openpyxl import load_workbook

from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment
)

from openpyxl.chart import (
    PieChart,
    Reference,
    BarChart
)

from openpyxl.chart.label import DataLabelList

from openpyxl.utils import get_column_letter



# ==========================================
# AJUSTAR COLUNAS
# ==========================================


def ajustar_largura_colunas(planilha):

    for coluna in planilha.columns:

        maior = 0

        letra = get_column_letter(
            coluna[0].column
        )


        for celula in coluna:

            if celula.value:

                tamanho = len(
                    str(celula.value)
                )

                if tamanho > maior:
                    maior = tamanho


        planilha.column_dimensions[
            letra
        ].width = maior + 3




# ==========================================
# CABEÇALHO
# ==========================================


def estilizar_cabecalho(planilha):

    preenchimento = PatternFill(
        "solid",
        fgColor="1F4E78"
    )


    for celula in planilha[1]:

        celula.font = Font(
            bold=True,
            color="FFFFFF"
        )

        celula.fill = preenchimento

        celula.alignment = Alignment(
            horizontal="center"
        )




# ==========================================
# FILTROS
# ==========================================


def aplicar_filtro(planilha):

    planilha.auto_filter.ref = (
        planilha.dimensions
    )



def congelar_cabecalho(planilha):

    planilha.freeze_panes = "A2"





# ==========================================
# FORMATAR PLANILHAS
# ==========================================


def formatar_planilhas(caminho):

    wb = load_workbook(
        caminho
    )


    for nome in wb.sheetnames:

        ws = wb[nome]


        estilizar_cabecalho(
            ws
        )


        ajustar_largura_colunas(
            ws
        )


        aplicar_filtro(
            ws
        )


        congelar_cabecalho(
            ws
        )


    wb.save(
        caminho
    )





# ==========================================
# CRIAR DASHBOARD
# ==========================================


def criar_dashboard(caminho):

    wb = load_workbook(caminho)


    if "Dashboard IA" in wb.sheetnames:
        del wb["Dashboard IA"]


    dashboard = wb.create_sheet(
        "Dashboard IA",
        0
    )


    # ==============================
    # TÍTULO
    # ==============================

    dashboard["A1"] = "RELATÓRIO DE DESEMPENHO DA IA"

    dashboard.merge_cells(
        "A1:J1"
    )

    dashboard["A1"].alignment = Alignment(
        horizontal="center"
    )

    dashboard["A1"].font = Font(
        bold=True,
        size=16
    )


    # ==============================
    # TAMANHO DAS COLUNAS
    # ==============================

    larguras = {

        "A":20,
        "B":15,
        "C":5,

        "D":25,
        "E":15,
        "F":5,

        "G":20,
        "H":15,
        "I":5,

        "J":15,
        "K":15

    }


    for coluna, largura in larguras.items():

        dashboard.column_dimensions[coluna].width = largura



    # ==============================
    # CARDS KPI
    # ==============================


    cards = [

        (
            "A3",
            "A4",
            "TOTAL ANALISADO",
            "=COUNTA('Dados Analisados'!A:A)-1"
        ),


        (
            "D3",
            "D4",
            "PROBLEMAS CONFIRMADOS",
            '=COUNTIF(\'Dados Analisados\'!G:G,"Problema confirmado")'
        ),


        (
            "G3",
            "G4",
            "FALSOS POSITIVOS",
            '=COUNTIF(\'Dados Analisados\'!G:G,"Falso positivo")'
        ),


        (
            "J3",
            "J4",
            "PENDENTES",
            '=COUNTIF(\'Dados Analisados\'!G:G,"Pendente")'
        )

    ]



    for titulo, valor, nome, formula in cards:


        dashboard.merge_cells(
            f"{titulo}:{chr(ord(titulo[0])+1)}3"
        )


        dashboard.merge_cells(
            f"{valor}:{chr(ord(valor[0])+1)}4"
        )


        dashboard[titulo] = nome


        dashboard[titulo].font = Font(
            bold=True,
            size=11
        )


        dashboard[titulo].alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
        )



        dashboard[valor] = formula


        dashboard[valor].font = Font(
            bold=True,
            size=20
        )


        dashboard[valor].alignment = Alignment(
            horizontal="center",
            vertical="center"
        )



    dashboard.row_dimensions[3].height = 35
    dashboard.row_dimensions[4].height = 35




    # ==============================
    # TABELA AUXILIAR DO GRÁFICO
    # ==============================


    dashboard["A7"] = "Indicador"
    dashboard["B7"] = "Quantidade"


    tabela = [

        (
            "Problemas confirmados",
            '=COUNTIF(\'Dados Analisados\'!G:G,"Problema confirmado")'
        ),


        (
            "Falsos positivos",
            '=COUNTIF(\'Dados Analisados\'!G:G,"Falso positivo")'
        ),


        (
            "Pendentes",
            '=COUNTIF(\'Dados Analisados\'!G:G,"Pendente")'
        )

    ]


    linha = 8


    for nome, formula in tabela:


        dashboard.cell(
            linha,
            1,
            nome
        )


        dashboard.cell(
            linha,
            2,
            formula
        )


        linha +=1




    # ==============================
    # GRÁFICO PIZZA
    # ==============================


    grafico = PieChart()


    grafico.title = "Distribuição das Detecções"



    dados = Reference(

        dashboard,

        min_col=2,

        min_row=7,

        max_row=10

    )


    categorias = Reference(

        dashboard,

        min_col=1,

        min_row=8,

        max_row=10

    )


    grafico.add_data(

        dados,

        titles_from_data=True

    )


    grafico.set_categories(

        categorias

    )


    grafico.height = 12
    grafico.width = 18



    grafico.dataLabels = DataLabelList()

    grafico.dataLabels.showPercent = True

    grafico.dataLabels.showVal = True



    dashboard.add_chart(

        grafico,

        "D7"

    )

    # =====================================
    # GRÁFICO DE CONFUSÕES DA IA
    # =====================================


    ws_dados = wb["Dados Analisados"]


    # Criar tabela auxiliar

    linha_inicio = 15


    dashboard[f"A{linha_inicio}"] = "Confusão IA x Humano"
    dashboard[f"B{linha_inicio}"] = "Quantidade"


    confusoes = (

        ws_dados

        .values

    )


    from collections import Counter


    contador = Counter()


    for linha in list(confusoes)[1:]:

        ia = linha[2]

        humano = linha[4]


        if (
            humano != "-"
            and humano != "Desconhecido"
        ):

            if (
                ia.lower()
                not in humano.lower()
            ):

                contador[
                    f"{ia} → {humano}"
                ] += 1



    linha = linha_inicio + 1


    for problema, quantidade in contador.items():

        dashboard.cell(
            linha,
            1,
            problema
        )

        dashboard.cell(
            linha,
            2,
            quantidade
        )

        linha += 1



    grafico_barras = BarChart()


    grafico_barras.title = (
        "Principais Confusões da IA"
    )


    grafico_barras.y_axis.title = (
        "Quantidade"
    )


    grafico_barras.x_axis.title = (
        "Erro de classificação"
    )



    dados = Reference(

        dashboard,

        min_col=2,

        min_row=linha_inicio,

        max_row=linha-1

    )


    categorias = Reference(

        dashboard,

        min_col=1,

        min_row=linha_inicio+1,

        max_row=linha-1

    )



    grafico_barras.add_data(

        dados,

        titles_from_data=True

    )



    grafico_barras.set_categories(

        categorias

    )



    grafico_barras.height = 10

    grafico_barras.width = 20



    dashboard.add_chart(

        grafico_barras,

        "K7"

    )



    wb.save(
        caminho
    )




# ==========================================
# EXECUÇÃO
# ==========================================


def gerar_relatorio_visual(caminho):


    formatar_planilhas(
        caminho
    )


    criar_dashboard(
        caminho
    )






if __name__ == "__main__":


    arquivo = (

        r"C:\Users\marcelino.santos\Desktop"

        r"\Projetos\road-ai-analytics"

        r"\relatorios-gerados"

        r"\Relatorio_Tecnico_IA.xlsx"

    )


    gerar_relatorio_visual(

        arquivo

    )


    print(
        "Relatório formatado com sucesso!"
    )