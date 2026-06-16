#!/usr/bin/env python3
"""Server for Sta da jedem app"""
import json, os, urllib.request, urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

DS_URL = "https://api.deepseek.com/chat/completions"
PORT = 8080
DIR = os.path.dirname(os.path.abspath(__file__))

def get_key():
    env_path = os.path.expanduser("~/.hermes/.env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("DEEPSEEK_API_KEY"):
                return line.split("=", 1)[1].strip()
    return ""

DS_KEY = get_key()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_POST(self):
        if self.path == "/api/cook":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            ingredients = body.get("ingredients", "")
            re_roll = body.get("re_roll", False)
            seen = body.get("seen", [])

            rr = ""
            if re_roll and seen:
                rr = f"\nVIKTIGT: Generera ett HELT ANNAT recept. INTE något av dessa: {', '.join(seen)}. Var kreativ och hitta på något nytt."
            elif re_roll:
                rr = "\nGe mig ett HELT ANNAT recept — inte samma som tidigare."
            
            prompt = f"""Jag har dessa ingredienser: {ingredients}

Hitta på ETT enkelt recept. Formatera:
### Rättens namn

**Tid:** X min
**Svårighet:** lätt/medel/svår

**Ingredienser:**
- ingrediens (mängd)

**Tillagning:**
1. steg

**Tips:** en mening

Om en viktig ingrediens saknas, nämn det. Svara på svenska.{rr}"""

            try:
                data = json.dumps({
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                    "temperature": 0.8
                }).encode()

                req = urllib.request.Request(DS_URL, data=data, headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DS_KEY}"
                })
                resp = urllib.request.urlopen(req, timeout=45)
                recipe = json.loads(resp.read())["choices"][0]["message"]["content"]

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"recipe": recipe}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    print(f"🍳 Server: http://localhost:{PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
