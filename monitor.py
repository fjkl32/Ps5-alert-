
import os
import re
import json
import urllib.request
import urllib.error
from html import unescape

URL = "https://www.playstation.com/pt-pt/accessories/dualsense-wireless-controller/buy-now/product/grand-theft-auto-vi-black-limited-edition/"
WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]

def get_page():
    req = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return unescape(response.read().decode("utf-8", errors="ignore"))

def detect_status(html):
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).lower()

    if "adicionar ao carrinho" in text or "comprar agora" in text:
        return "AVAILABLE"

    if "esgotado" in text or "indisponível" in text:
        return "UNAVAILABLE"

    if "reservar" in text:
        return "RESERVATION"

    return "UNKNOWN"

def send_alert(status):
    message = {
        "content": (
            "🎮 **Possível disponibilidade do comando GTA VI!**\n"
            "A página da PlayStation apresenta um estado de compra diferente.\n"
            f"Estado detetado: **{status}**\n"
            f"👉 {URL}\n"
            "Confirma a disponibilidade antes de concluir a compra."
        )
    }

    data = json.dumps(message).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    urllib.request.urlopen(req, timeout=20)

def main():
    html = get_page()
    status = detect_status(html)

    state_file = "state.txt"
    previous = "UNKNOWN"

    if os.path.exists(state_file):
        with open(state_file, "r") as file:
            previous = file.read().strip()

    print(f"Estado anterior: {previous}")
    print(f"Estado atual: {status}")

    if status == "AVAILABLE" and previous != "AVAILABLE":
        send_alert(status)

    with open(state_file, "w") as file:
        file.write(status)

if __name__ == "__main__":
    main()
