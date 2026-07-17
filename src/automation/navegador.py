import asyncio
import os
import pandas as pd

from playwright.async_api import async_playwright
from src.config.config import URL
from src.automation.login import realizar_login


# ==========================================
# 1. FUNÇÕES ASSÍNCRONAS
# ==========================================


async def acessar_lista_detecoes(pagina, data_inicio, data_fim):

    print("\nAbrindo o menu Rodovia...")

    await pagina.locator('a[href="#highway"]').click()
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



        await pagina_principal.goto(URL)


        await pagina_principal.wait_for_load_state(
            "networkidle"
        )



        await realizar_login(
            pagina_principal
        )


        await pagina_principal.wait_for_load_state(
            "networkidle"
        )



        await acessar_lista_detecoes(
            pagina_principal,
            data_inicio_input,
            data_fim_input
        )



        todos_os_dados = []



        print("\nLendo Página 1...")


        dados_pag_1 = await extrair_dados_tabela(
            pagina_principal
        )


        todos_os_dados.extend(
            dados_pag_1
        )



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
                    f"\nExtraindo páginas {pagina_atual} até {pagina_atual + 4}"
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
        # ANÁLISE
        # ==========================================


        df = pd.DataFrame(
            todos_os_dados
        )



        # Remove objetos ainda não avaliados

        df_avaliado = df[
            df["Objeto Real"].str.strip() != "-"
        ].copy()



        def comparar_ia_humano(row):


            ia = (
                row["IA Detectou"]
                .strip()
                .lower()
            )


            humano = (
                row["Objeto Real"]
                .strip()
                .lower()
            )



            if ia == humano:

                return "Acerto"

            else:

                return "Erro"




        df_avaliado["Resultado"] = (
            df_avaliado.apply(
                comparar_ia_humano,
                axis=1
            )
        )




        # ==========================================
        # MÉTRICAS GERAIS
        # ==========================================


        total_capturado = len(df)


        total_avaliado = len(df_avaliado)



        acertos = (
            df_avaliado["Resultado"]
            ==
            "Acerto"
        ).sum()



        erros = (
            df_avaliado["Resultado"]
            ==
            "Erro"
        ).sum()



        metricas = pd.DataFrame({

            "Métrica":[

                "Total imagens capturadas",

                "Imagens avaliadas",

                "Acertos",

                "Erros de detecção"

            ],


            "Valor":[

                total_capturado,

                total_avaliado,

                acertos,

                erros

            ]

        })




        # ==========================================
        # ANÁLISE POR PROBLEMA
        # ==========================================


        analise_objeto = df_avaliado.groupby(
            "Objeto Real"
        ).agg(


            Total_Avaliado=(

                "Objeto Real",

                "count"

            ),



            Acertos=(

                "Resultado",

                lambda x:
                (x == "Acerto").sum()

            ),



            Erros=(

                "Resultado",

                lambda x:
                (x == "Erro").sum()

            )


        ).reset_index()





        # ==========================================
        # EXPORTAÇÃO EXCEL
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

                sheet_name="Análise por Problema",

                index=False

            )





        print("\n===================================")

        print("RELATÓRIO GERADO COM SUCESSO")

        print("===================================")


        print(
            f"Arquivo salvo em:\n{arquivo}"
        )



        await navegador.close()






# ==========================================
# 3. EXECUÇÃO
# ==========================================


if __name__ == "__main__":

    asyncio.run(main())