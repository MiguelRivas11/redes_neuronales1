from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests

URL = "https://ayard007.github.io/Inteligencia-Artificial-Profunda/proyecto_final_chatbots_UNE.html"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    # Abrir la página
    page.goto(URL)

    # Esperar a que cargue completamente
    page.wait_for_timeout(5000)

    # Obtener HTML renderizado
    html = page.content()

    browser.close()

# Parsear HTML
soup = BeautifulSoup(html, "html.parser")

# Eliminar scripts y estilos
for tag in soup(["script", "style"]):
    tag.decompose()

# Obtener texto limpio
texto = soup.get_text(separator="\n")

# Limpiar líneas vacías
texto = "\n".join(
    line.strip() for line in texto.splitlines() if line.strip()
)

print(texto[:10000])  # primeros 10k caracteres