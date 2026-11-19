
import os
import re
import json
import urllib.request
import urllib.error
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
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
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
            "Produto não encontrado na página."
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

    # Se a mensagem já desapareceu, usar a primeira
    # secção encontrada para comparar com o estado anterior.
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
        print("A mensagem de indisponibilidade desapareceu!")
        send_alert(area)

    elif current_status == "unavailable":
        print("Continua indisponível.")

    else:
        print("O texto continua alterado. Sem nova notificação.")

    with open(state_file, "w") as file:
        file.write(current_status)


if __name__ == "__main__":
    main()
