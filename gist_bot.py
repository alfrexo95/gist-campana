import requests
import os
import random
import re
import urllib.parse
from datetime import datetime

# --- CONFIGURACIÓN ---
PAT_TOKEN = os.environ.get("PAT_TOKEN")
PIEFED_USER = os.environ.get("PIEFED_USER")
PIEFED_PASS = os.environ.get("PIEFED_PASS")
GIST_ID = "4c1dea8f2b1ec60aff12af268b8e4a24"
HEADERS = {"Authorization": f"token {PAT_TOKEN}", "Accept": "application/vnd.github.v3+json"}

BTC = "bc1qt3rukpe7qp737zj5j5xpxxmcqv90cfefhg5e00"
ETH = "0xA5E6eB31868A85127B1ED82b8C760193356206ED"
LTC = "ltc1qdyyg99l8ehp9aj4ehzvmefglmpl9750226k7ne"
LN = "chieftrait089@walletofsatoshi.com"

CTAS = [
    "Supporting this charity can change lives. Donating is a great action, but sharing it so it reaches more people is even better.",
    "Little by little, grain by grain, a bucket gets filled. Your contribution matters.",
    "The hardest path is the one you never start. The first step is what counts.",
    "Helping is rewarding. See for yourself."
]

def generar_qr(data):
    encoded = urllib.parse.quote(data)
    return f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={encoded}"

def actualizar_gist_progreso():
    print("  📝 Actualizando Gist con barra de progreso, QR y fecha...")
    url = f"https://api.github.com/gists/{GIST_ID}"
    res = requests.get(url, headers=HEADERS)
    
    if res.status_code != 200:
        print(f"  ❌ No se pudo obtener el Gist (Error {res.status_code}).")
        return False

    files = res.json()["files"]
    filename = list(files.keys())[0]
    contenido = files[filename]["content"]
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    barra_url = "https://progress-bar.dev/44/?scale=2600&title=Raised&width=400&color=f7931a"
    bloque_progreso = f"## 💰 Campaign Progress\n![Progress]({barra_url})\n**$44 USD Raised out of $2600+ Goal** *(Last updated: {fecha_actual})*\n\n"
    
    bloque_qr = "## 📲 Scan to Donate\n"
    bloque_qr += f"**BTC**\n![BTC QR]({generar_qr(BTC)})\n`{BTC}`\n\n"
    bloque_qr += f"**ETH**\n![ETH QR]({generar_qr(ETH)})\n`{ETH}`\n\n"
    bloque_qr += f"**LTC**\n![LTC QR]({generar_qr(LTC)})\n`{LTC}`\n\n"
    bloque_qr += f"**⚡ Lightning**\n![LN QR]({generar_qr('lightning:' + LN)})\n`{LN}`\n\n---\n\n"

    if "## 💰 Campaign Progress" in contenido:
        contenido = re.sub(r"## 💰 Campaign Progress.*?\n\n", bloque_progreso, contenido, flags=re.DOTALL)
    else:
        contenido = contenido.replace("# 🇨🇺 Direct Relief for Cuban Families", f"# 🇨🇺 Direct Relief for Cuban Families\n\n{bloque_progreso}")
    
    if "## 📲 Scan to Donate" not in contenido:
        contenido = contenido.replace("**How You Can Help:**", f"{bloque_qr}**How You Can Help:**")

    data = {"description": "🚨 Direct Relief for Cuban Families", "files": {filename: {"content": contenido}}}
    res = requests.patch(url, headers=HEADERS, json=data)
    if res.status_code == 200:
        print("  ✅ Gist actualizado correctamente.")
        return True
    else:
        print(f"  ❌ Error actualizando Gist: {res.status_code}")
        return False

def publicar_en_piefed(mensaje):
    if not PIEFED_USER or not PIEFED_PASS:
        print("    - PieFed: Omitido (faltan credenciales)")
        return False
    try:
        print("  🐘 Publicando en PieFed (c/Fundraising)...")
        # ENDPOINT CORREGIDO: /api/alpha/ en lugar de /api/v3/
        base_url = "https://piefed.social/api/alpha"
        
        # 1. Login usando el endpoint correcto
        login_res = requests.post(f"{base_url}/user/login", json={
            "username": PIEFED_USER,
            "password": PIEFED_PASS
        }, timeout=15)
        
        if login_res.status_code != 200:
            print(f"    - PieFed Login Error: {login_res.status_code} - {login_res.text}")
            return False
            
        jwt = login_res.json().get("jwt")
        if not jwt:
            print("    - PieFed: No se obtuvo el token JWT.")
            return False
        
        # 2. Buscar la comunidad c/Fundraising
        comm_id = None
        # Intentar búsqueda directa por nombre
        comm_res = requests.get(f"{base_url}/community", params={"name": "fundraising"}, timeout=15)
        if comm_res.status_code == 200:
            # La respuesta puede ser un objeto o una lista
            data = comm_res.json()
            if isinstance(data, dict) and "community_view" in data:
                comm_id = data["community_view"]["community"]["id"]
            elif isinstance(data, list) and len(data) > 0:
                comm_id = data[0]["community"]["id"]
        
        if not comm_id:
            # Intentar búsqueda general si la directa falla
            search_res = requests.get(f"{base_url}/search", params={"q": "fundraising", "type_": "Communities"}, timeout=15)
            if search_res.status_code == 200:
                for c in search_res.json().get("communities", []):
                    if "fundraising" in c["community"]["name"].lower():
                        comm_id = c["community"]["id"]
                        break
                        
        if comm_id:
            # 3. Crear el post usando el endpoint /post
            post_res = requests.post(f"{base_url}/post", json={
                "name": "Direct Relief for Cuban Families",
                "body": mensaje,
                "community_id": comm_id,
                "auth": jwt
            }, timeout=15)
            
            if post_res.status_code in [200, 201]:
                print("    - PieFed: 200 (Publicado exitosamente)")
                return True
            else:
                print(f"    - PieFed Post Error: {post_res.status_code} - {post_res.text}")
        else:
            print("    - PieFed: No se encontró la comunidad c/Fundraising.")
    except Exception as e:
        print(f"    - Error en PieFed: {e}")
    return False

def publicar_en_foros():
    print(f"  📢 Compartiendo el Gist en foros...")
    mensaje_apoyo = random.choice(CTAS)
    gist_url = f"https://gist.github.com/alfrexo95/{GIST_ID}"
    mensaje = f"🇨🇺 **Direct Relief for Cuban Families**\n\n{mensaje_apoyo}\n\nSee the evidence and donation addresses here:\n{gist_url}\n\n#Cuba #Bitcoin #Solidarity"
    
    temp_file = "temp_message.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(mensaje)

    foros = [
        ("POST", "https://free.intcount.com/api/botchan/post", {"content": mensaje, "tag": "meta"}),
        ("POST", "https://anystation.net/", {"content": mensaje}),
        ("POST", "https://paste.rs/", mensaje),
        ("POST", "https://dpaste.com/api/v2/", {"content": mensaje}),
        ("POST", "https://snippet.host/", {"content": mensaje}),
        ("POST", "https://paste.c-net.org/", mensaje),
        ("POST", "https://pastebin.ai/api/v1/paste", {"content": mensaje}),
        ("POST", "https://brewpage.app/api/html?format=markdown", {"content": mensaje}),
        ("TELEGRAPH", "https://api.telegra.ph/createPage", {"title": "Cuba Relief", "content": mensaje}),
        ("POST", "https://termbin.com/", mensaje),
        ("POST", "https://hastebin.com/documents", mensaje),
        ("POST", "http://ix.io", {"f": mensaje}),
        ("POST", "https://fiche.rs", {"text": mensaje}),
        ("FILE", "https://envs.sh", "file"),
        ("FILE", "https://0x0.st", "file"),
        ("POST", "https://paste.centos.org/api/create", {"text": mensaje}),
        ("POST", "https://paste.debian.net/", {"text": mensaje}),
    ]
    
    exitos = 0
    for method, url, payload in foros:
        try:
            if method == "POST":
                res = requests.post(url, data=payload, timeout=15)
                print(f"    - {url.split('/')[2]}: {res.status_code}")
                if res.status_code in [200, 201]: exitos += 1
            elif method == "FILE":
                with open(temp_file, "rb") as f:
                    res = requests.post(url, files={payload: f}, timeout=30)
                print(f"    - {url.split('/')[2]}: {res.status_code}")
                if res.status_code in [200, 201]: exitos += 1
            elif method == "TELEGRAPH":
                acc_res = requests.post("https://api.telegra.ph/createAccount", json={"short_name": "CubaRelief", "author_name": "PredathorHaley"})
                if acc_res.status_code == 200:
                    payload['access_token'] = acc_res.json()['result']['access_token']
                    res = requests.post(url, json=payload, timeout=15)
                    print(f"    - telegra.ph: {res.status_code}")
                    if res.status_code == 200: exitos += 1
        except Exception as e:
            print(f"    - Error en {url}: {e}")
    
    if os.path.exists(temp_file): os.remove(temp_file)
    print(f"  ✅ Compartido en {exitos} plataformas de foros/pastebins.")

if __name__ == "__main__":
    actualizar_gist_progreso()
    publicar_en_foros()
    
    gist_url = f"https://gist.github.com/alfrexo95/{GIST_ID}"
    mensaje_piefed = f"🇨🇺 **Direct Relief for Cuban Families**\n\nSee the evidence and donation addresses here: {gist_url}"
    publicar_en_piefed(mensaje_piefed)
