
import os
import re
import json
import hashlib
import urllib.request
import urllib.error
from html.parser import HTMLParser
from html import unescape

URL = "https://www.playstation.com/pt-pt/accessories/dualsense-wireless-controller/buy-now/product/grand-theft-auto-vi-black-limited-edition/"

WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]

PRODUCT = "Comando sem fios DualSense® - Edição limitada Grand Theft Auto VI Black"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def get_page():
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_product_area(html):
    parser = TextExtractor()
    parser.feed(html)

    text = unescape(" ".join(parser.parts))
    text = re.sub(r"\s+", " ", text)

    positions = [
        m.start()
        for m in re.finditer(
            re.escape(PRODUCT),
            text,
            re.IGNORECASE
        )
    ]

    if not positions:
        raise RuntimeError(
            "Não foi possível localizar o produto na página."
        )

    candidates = []

    for position in positions:
        area = text[
            max(0, position - 500):
            position + 900
        ]

        if "84,99" in area:
            candidates.append(area)

    if not candidates:
        raise RuntimeError(
            "Não foi possível identificar a secção do produto."
        )

    return candidates[0]


def send_alert(area):
    message = (
        "🔔 **Alteração na página do comando GTA VI Black!**\n"
        "A secção do produto foi alterada. "
        "Confirma se já podes reservar ou comprar.\n\n"
        f"Trecho atualizado: {area[:1200]}\n\n"
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

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            print("Notificação Discord:", response.status)

    except urllib.error.HTTPError as e:
        print("ERRO DISCORD:", e.code)
        print("MOTIVO:", e.reason)
        print(
            "RESPOSTA:",
            e.read().decode("utf-8", errors="replace")
        )
        raise

    except urllib.error.URLError as e:
        print("ERRO DE LIGAÇÃO AO DISCORD:", e.reason)
        raise


def main():
    print("A consultar a página PlayStation...")

    html = get_page()
    area = extract_product_area(html)

    signature = hashlib.sha256(
        area.encode("utf-8")
    ).hexdigest()

    state_file = "state.txt"

    if os.path.exists(state_file):
        with open(state_file, "r") as file:
            previous = file.read().strip()
    else:
        previous = ""

    if not previous:
        print("Primeira verificação. Estado inicial guardado.")

    elif signature != previous:
        print("Alteração detetada!")
        send_alert(area)

    else:
        print("Sem alterações na secção do produto.")

    with open(state_file, "w") as file:
        file.write(signature)


if __name__ == "__main__":
    main()
