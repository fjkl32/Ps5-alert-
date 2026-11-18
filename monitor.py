
import os
import json
import urllib.request

URL = "https://www.playstation.com/pt-pt/accessories/dualsense-wireless-controller/buy-now/product/grand-theft-auto-vi-black-limited-edition/"
WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]

def send_alert(message):
    data = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        print("Discord respondeu:", response.status)

def main():
    print("A testar ligação ao Discord...")
    send_alert(
        "🧪 Teste do bot GTA VI: ligação ao Discord estabelecida!\n" + URL
    )

if __name__ == "__main__":
    main()
