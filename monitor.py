
import os
import re
import json
import time
import urllib.request
import urllib.error
import http.client
from html.parser import HTMLParser
from html import unescape

URL = "https://www.playstation.com/pt-pt/accessories/dualsense-wireless-controller/buy-now/product/grand-theft-auto-vi-black-limited-edition/"

WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]

PRODUCT = "Comando sem fios DualSense® - Edição limitada Grand Theft Auto VI Black"
TARGET_TEXT = "Não disponível para compra"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def normalize(text):
    return re.sub(
        r"\s+",
        " ",
        unescape(text)
    ).strip().lower()


def get_page():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
        "Connection": "close"
    }

    last_error = None

    for attempt in range(1, 6):
        try:
            print(f"Pedido à PlayStation: tentativa {attempt}/5")

            req = urllib.request.Request(
                URL,
                headers=headers
            )

            with urllib.request.urlopen(req, timeout=45) as response:
                html = response.read().decode(
                    "utf-8",
                    errors="replace"
                )

            if len(html) < 10000:
                raise RuntimeError("Página recebida demasiado pequena.")

            print(f"Página recebida: {len(html)} caracteres")
            return html

        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            ConnectionError,
            http.client.HTTPException,
            OSError,
            RuntimeError
        ) as error:
            last_error = error
            print(f"Falha na tentativa {attempt}: {error}")

            if attempt < 5:
                wait = attempt * 10
                print(f"Nova tentativa em {wait} segundos...")
                time.sleep(wait)

    raise RuntimeError(
        f"Não foi possível obter a página após 5 tentativas: {last_error}"
    )


def extract_product_area(html):
    parser = TextExtractor()
    parser.feed(html)

    text = normalize(" ".join(parser.parts))
    product = normalize(PRODUCT)

    positions = [
        match.start()
        for match in re.finditer(
            re.escape(product),
            text
        )
    ]

    if not positions:
        raise RuntimeError(
            "Produto não encontrado. Estado não será alterado."
        )

    target = normalize(TARGET_TEXT)
    candidates = []

    for position in positions:
        area = text[
            max(0, position - 1500):
            position + 4000
        ]

        candidates.append(area)

        if target in area:
            return area

    return candidates[0]


def detect_status(area):
    if normalize(TARGET_TEXT) in area:
        return "unavailable"

    return "changed"


def send_alert(area):
    message = (
        "🔔 **ALTERAÇÃO DETETADA NO COMANDO GTA VI BLACK!**\n\n"
        "A mensagem 'Não disponível para compra' "
        "deixou de aparecer na secção do produto.\n\n"
        "Isto pode indicar uma alteração na disponibilidade, "
        "mas não confirma stock.\n\n"
        f"Texto atual: {area[:1000]}\n\n"
        f"👉 {URL}"
    )

    data = json.dumps({
        "content": message
    }).encode("utf-8")

    req = urllib.request.Request(
        WEBHOOK,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://github.com, 1.0)",
            "Accept": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        print("Notificação Discord:", response.status)


def main():
    print("A consultar a página PlayStation...")

    html = get_page()
    area = extract_product_area(html)

    current_status = detect_status(area)

    state_file = "state.txt"

    if os.path.exists(state_file):
        with open(state_file, "r") as file:
            previous_status = file.read().strip()
    else:
        previous_status = ""

    print("Estado atual:", current_status)
    print("Estado anterior:", previous_status)

    if not previous_status:
        print("Primeira verificação. Estado inicial guardado.")

    elif (
        previous_status == "unavailable"
        and current_status == "changed"
    ):
        print("Alteração detetada!")
        send_alert(area)

    elif current_status == "unavailable":
        print("Continua indisponível.")

    else:
        print("O texto continua alterado. Sem nova notificação.")

    with open(state_file, "w") as file:
        file.write(current_status)


if __name__ == "__main__":
    main()
