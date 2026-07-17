# Certifique-se de importar o que for necessário se houver constantes
from src.config.config import USUARIO, SENHA

async def realizar_login(page):
    print("Realizando login...")
    # Todas as ações de navegador no modo assíncrono PRECISAM de 'await'
    await page.fill("#id_email", USUARIO)
    await page.fill("#id_password", SENHA)
    await page.get_by_role("button", name="Login").click()
    print("Login concluído!")