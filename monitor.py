
import os
import json
import urllib.request
import urllib.error

URL = "https://www.playstation.com/pt-pt/accessories/dualsense-wireless-controller/buy-now/product/grand-theft-auto-vi-black-limited-edition/"

WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")


def send_alert(message):
    if not WEBHOOK:
        raise ValueError("Secret DISCORD_WEBHOOK_URL não encontrado.")

    data = json.dumps({
        "content": message
    }).encode("utf-8")

    request = urllib.request.Request(
        WEBHOOK,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "PS5-Stock-Monitor/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            print("Discord respondeu:", response.status)
            print("Webhook a funcionar corretamente.")

    except urllib.error.HTTPError as error:
        print("Erro HTTP:", error.code)
        print("Resposta Discord:", error.read().decode("utf-8"))
        raise

    except urllib.error.URLError as error:
        print("Erro de ligação:", error.reason)
        raise


def main():
    print("A testar ligação ao Discord...")
    print("Página monitorizada:", URL)

    send_alert(
        "🧪 **TESTE DO BOT GTA VI**\n"
        "A ligação ao Discord está a ser testada.\n"
        + URL
    )


if __name__ == "__main__":
    main()
