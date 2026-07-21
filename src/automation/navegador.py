import asyncio
import os
import pandas as pd

from src.analytics.familias import identificar_familia

from playwright.async_api import async_playwright

from src.config.config import URL
from src.automation.login import realizar_login

from src.analytics.avaliador_ia import (
    avaliar_deteccao,
    avaliar_classificacao
)


# ==========================================
# 1. FUNÇÕES ASSÍNCRONAS
# ==========================================


async def acessar_lista_detecoes(pagina, data_inicio, data_fim):

    print("\nAbrindo o menu Rodovia...")

    await pagina.locator(
        'a[href="#highway"]'
    ).click()

    await pagina.wait_for_timeout(500)


    print("Clicando em Triagem...")


    await pagina.locator(
        'a[href="/highway/triage/"]'
    ).click()


    await pagina.wait_for_load_state(
        "networkidle"
    )


    print("Preenchendo filtros...")


    await pagina.locator(
        "#id_status"
    ).select_option(
        "captured"
    )


    await pagina.locator(
        "#id_start_datetime"
    ).fill(
        data_inicio
    )


    await pagina.locator(
        "#id_end_datetime"
    ).fill(
        data_fim
    )


    print("Aplicando filtros...")


    await pagina.get_by_role(
        "button",
        name="Filtrar"
    ).click()


    await pagina.wait_for_load_state(
        "networkidle"
    )





async def extrair_dados_tabela(pagina):

    linhas = await pagina.locator(
        "tr[data-object-id]"
    ).all()


    dados_extraidos = []


    for linha in linhas:

        colunas = linha.locator(
            "td"
        )


        if await colunas.count() >= 6:


            dados_extraidos.append({

                "Camera":
                    (
                        await colunas.nth(1)
                        .inner_text()
                    ).strip(),


                "Veiculo":
                    (
                        await colunas.nth(2)
                        .inner_text()
                    ).strip(),


                "IA Detectou":
                    (
                        await colunas.nth(3)
                        .inner_text()
                    ).strip(),


                "Data":
                    (
                        await colunas.nth(4)
                        .inner_text()
                    ).strip(),


                "Objeto Real":
                    (
                        await colunas.nth(5)
                        .inner_text()
                    ).strip()

            })


    return dados_extraidos






async def processar_aba_paralela(
        contexto,
        url,
        numero_pagina
):


    nova_pagina = await contexto.new_page()


    await nova_pagina.goto(
        url
    )


    try:

        await nova_pagina.wait_for_load_state(
            "networkidle",
            timeout=10000
        )

    except:

        pass



    dados = await extrair_dados_tabela(
        nova_pagina
    )


    print(
        f"-> Página {numero_pagina}: {len(dados)} registros"
    )


    await nova_pagina.close()


    return dados




# ==========================================
# 2. EXECUÇÃO PRINCIPAL
# ==========================================


async def main():

    print("=======================================")
    print("   INICIANDO EXTRAÇÃO E ANÁLISE IA")
    print("=======================================")



    data_inicio_input = input(
        "Digite a data inicial (Ex: 15/07/2026 00:00): "
    )


    data_fim_input = input(
        "Digite a data final (Ex: 17/07/2026 12:00): "
    )



    async with async_playwright() as p:


        navegador = await p.chromium.launch(
            headless=True
        )


        contexto = await navegador.new_context()


        pagina_principal = await contexto.new_page()



        await pagina_principal.goto(
            URL
        )


        await pagina_principal.wait_for_load_state(
            "networkidle"
        )



        await realizar_login(
            pagina_principal
        )



        await acessar_lista_detecoes(
            pagina_principal,
            data_inicio_input,
            data_fim_input
        )



        todos_os_dados = []



        print("\nLendo Página 1...")


        todos_os_dados.extend(

            await extrair_dados_tabela(
                pagina_principal
            )

        )



        # ==========================
        # PAGINAÇÃO
        # ==========================


        botao_proxima = pagina_principal.locator(
            'a[aria-label="Next Page"]'
        )


        if await botao_proxima.is_visible():


            link_prox = await botao_proxima.get_attribute(
                "href"
            )


            url_base = pagina_principal.url.split('?')[0]


            parametros = link_prox.split('&page=')[0]


            url_base_paginas = (
                url_base
                +
                parametros
                +
                "&page="
            )


            pagina_atual = 2

            continuar = True

            ultima_pagina = []



            while continuar:


                tarefas = []


                print(
                    f"\nExtraindo páginas {pagina_atual} até {pagina_atual+4}"
                )


                for i in range(5):

                    numero = pagina_atual + i


                    tarefas.append(

                        processar_aba_paralela(
                            contexto,
                            f"{url_base_paginas}{numero}",
                            numero
                        )

                    )


                resultados = await asyncio.gather(
                    *tarefas
                )



                for dados in resultados:


                    if len(dados) == 0:

                        continuar = False
                        break


                    if dados == ultima_pagina:

                        continuar = False
                        break



                    todos_os_dados.extend(
                        dados
                    )


                    ultima_pagina = dados



                pagina_atual += 5



                if pagina_atual > 200:

                    break





        print("\n=======================================")

        print(
            f"TOTAL EXTRAÍDO: {len(todos_os_dados)}"
        )

        print("=======================================")



        # ==========================================
        # ANÁLISE IA
        # ==========================================


        df = pd.DataFrame(
            todos_os_dados
        )

        df["Família"] = df["Objeto Real"].apply(
            identificar_familia
        )

        df["Resultado Detecção"] = (

            df.apply(

                lambda row:

                avaliar_deteccao(
                    row["IA Detectou"],
                    row["Objeto Real"]
                ),

                axis=1

            )

        )

        print(
            df["Resultado Detecção"].value_counts()
        )

        print(
            "\nRegistros 'Não confirmado':"
        )

        print(
            df[
                df["Resultado Detecção"]
                ==
                "Não confirmado"
            ][
                [
                    "IA Detectou",
                    "Objeto Real",
                    "Data"
                ]
            ]
        )


        df["Resultado Classificação"] = (

            df.apply(

                lambda row:

                avaliar_classificacao(
                    row["IA Detectou"],
                    row["Objeto Real"]
                ),

                axis=1

            )

        )




        # ==========================================
        # MÉTRICAS
        # ==========================================


        metricas = pd.DataFrame({

            "Métrica":[

                "Total capturado",

                "Problemas confirmados",

                "Falsos positivos",

                "Pendentes",

                "Classificação correta",

                "Classe diferente"

            ],


            "Valor":[


                len(df),


                (
                    df["Resultado Detecção"]
                    ==
                    "Problema confirmado"
                ).sum(),



                (
                    df["Resultado Detecção"]
                    ==
                    "Falso positivo"
                ).sum(),



                (
                    df["Resultado Detecção"]
                    ==
                    "Pendente"
                ).sum(),



                (
                    df["Resultado Classificação"]
                    ==
                    "Classificação correta"
                ).sum(),



                (
                    df["Resultado Classificação"]
                    ==
                    "Classe diferente"
                ).sum()

            ]

        })





        # ==========================================
        # ANÁLISE POR PROBLEMA
        # ==========================================


        analise_objeto = (

            df.groupby(
                "Objeto Real"
            )

            .size()

            .reset_index(
                name="Quantidade"
            )

        )

        # ==========================================
        # MATRIZ DE ERROS DA IA
        # ==========================================
    
        matriz_erros = (

            df[

                df["Resultado Classificação"]

                ==

                "Classe diferente"

            ]

            .groupby(

                [
                    "IA Detectou",
                    "Objeto Real"
                ]

            )

            .size()

            .reset_index(

                name="Quantidade"

            )

            .sort_values(

                "Quantidade",

                ascending=False

            )

        )

        # ==========================================
        # DESEMPENHO POR CLASSE DA IA
        # ==========================================

        desempenho_ia = (

            df.groupby(
                "IA Detectou"
            )
            .agg(

                Total_Detectado=(
                    "IA Detectou",
                    "count"
                ),

                Problemas_Confirmados=(
                    "Resultado Detecção",
                    lambda x:
                    (
                        x == "Problema confirmado"
                    ).sum()
                ),

                Falsos_Positivos=(
                    "Resultado Detecção",
                    lambda x:
                    (
                        x == "Falso positivo"
                    ).sum()
                ),

                Pendentes=(
                    "Resultado Detecção",
                    lambda x:
                    (
                        x == "Pendente"
                    ).sum()
                ),

                Classificacoes_Corretas=(
                    "Resultado Classificação",
                    lambda x:
                    (
                        x == "Classificação correta"
                    ).sum()
                ),

                Classes_Diferentes=(
                    "Resultado Classificação",
                    lambda x:
                    (
                        x == "Classe diferente"
                    ).sum()
                )

            )

            .reset_index()

        )

        # ==========================================
        # EXPORTAÇÃO
        # ==========================================


        pasta = (
            r"C:\Users\marcelino.santos\Desktop"
            r"\Projetos\road-ai-analytics"
            r"\relatorios-gerados"
        )


        os.makedirs(
            pasta,
            exist_ok=True
        )



        arquivo = os.path.join(
            pasta,
            "Relatorio_Tecnico_IA.xlsx"
        )



        with pd.ExcelWriter(
            arquivo,
            engine="openpyxl"
        ) as writer:


            metricas.to_excel(
                writer,
                sheet_name="Métricas Gerais",
                index=False
            )


            analise_objeto.to_excel(
                writer,
                sheet_name="Análise Problemas",
                index=False
            )

            desempenho_ia.to_excel(
                writer,
                sheet_name="Desempenho IA",
                index=False
            )

            matriz_erros.to_excel(
                writer,
                sheet_name="Matriz de Erros",
                index=False
            )

            desempenho_ia.to_excel(
                writer,
                sheet_name="Desempenho IA",
                index=False
            )

            df.to_excel(
                writer,
                sheet_name="Dados Analisados",
                index=False
            )



        print("\n===================================")

        print(
            "RELATÓRIO GERADO COM SUCESSO"
        )

        print(
            arquivo
        )

        print("===================================")


        print("\n========== VALIDAÇÃO ==========")

        print(f"Total capturado: {len(df)}")

        print("\nResultado Detecção:")
        print(df["Resultado Detecção"].value_counts())

        print("\nResultado Classificação:")
        print(df["Resultado Classificação"].value_counts())

        print("\nFamílias:")
        print(df["Família"].value_counts())

        print("===============================\n")

        print("\nValores únicos da IA:")
        print(sorted(df["IA Detectou"].unique()))

        print("\nValores únicos do Objeto Real:")
        print(sorted(df["Objeto Real"].unique()))

        nao_identificados = df[
            df["Família"] == "Não identificado"
        ]

        print(f"\nNão identificados: {len(nao_identificados)}")

        if len(nao_identificados):
            print(nao_identificados[["IA Detectou", "Objeto Real"]])

        nao_mapeados = df[
            df["Resultado Detecção"] == "Objeto IA não mapeado"
        ]

        print(f"\nObjetos IA não mapeados: {len(nao_mapeados)}")

        if len(nao_mapeados):
            print(nao_mapeados[["IA Detectou", "Objeto Real"]])

        confirmados = (df["Resultado Detecção"] == "Problema confirmado").sum()
        falsos = (df["Resultado Detecção"] == "Falso positivo").sum()
        pendentes = (df["Resultado Detecção"] == "Pendente").sum()
        nao_confirmados = (df["Resultado Detecção"] == "Não confirmado").sum()

        print(
            f"{confirmados} + {falsos} + {pendentes} + {nao_confirmados}"
        )
        print("\nConferência:")
        print(f"{confirmados} + {falsos} + {pendentes} + {nao_confirmados} = {confirmados + falsos + pendentes + nao_confirmados}")
        print(f"Total capturado = {len(df)}")

        await navegador.close()




if __name__ == "__main__":

    asyncio.run(main())