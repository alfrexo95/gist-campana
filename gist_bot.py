import requests
import os
import random
import re
from datetime import datetime

# --- CONFIGURACIÓN ---
PAT_TOKEN = os.environ.get("PAT_TOKEN")
GIST_ID = "4c1dea8f2b1ec60aff12af268b8e4a24" # Tu Gist estático
HEADERS = {"Authorization": f"token {PAT_TOKEN}", "Accept": "application/vnd.github.v3+json"}

# Mensajes persuasivos traducidos al inglés
CTAS = [
    "Supporting this charity can change lives. Donating is a great action, but sharing it so it reaches more people is even better.",
    "Little by little, grain by grain, a bucket gets filled. Your contribution matters.",
    "The hardest path is the one you never start. The first step is what counts.",
    "Helping is rewarding. See for yourself."
]

def actualizar_gist_progreso():
    """Actualiza el Gist para mostrar los $44 recaudados manteniendo el resto del texto intacto."""
    print("  📝 Actualizando progreso en el Gist...")
    url = f"https://api.github.com/gists/{GIST_ID}"
    res = requests.get(url, headers=HEADERS)
    
    if res.status_code != 200:
        print(f"  ❌ No se pudo obtener el Gist (Error {res.status_code}).")
        return False

    files = res.json()["files"]
    filename = list(files.keys())[0]
    contenido_actual = files[filename]["content"]

    # Texto del progreso
    progreso_texto = "## 💰 Current Progress: **$44 USD Raised** (Thank you!)\n\n"
    
    if "## 💰 Current Progress:" in contenido_actual:
        # Si ya existe, lo reemplazamos
        contenido_actual = re.sub(r"## 💰 Current Progress:.*?\n\n", progreso_texto, contenido_actual, flags=re.DOTALL)
    else:
        # Si no existe, lo insertamos justo debajo del título principal
        contenido_actual = contenido_actual.replace(
            "# 🇨🇺 Direct Relief for Cuban Families", 
            f"# 🇨🇺 Direct Relief for Cuban Families\n\n{progreso_texto}"
        )

    # Enviar la actualización a GitHub
    data = {
        "description": "🚨 Direct Relief for Cuban Families - Crypto Donations Accepted",
        "files": {filename: {"content": contenido_actual}}
    }
    res = requests.patch(url, headers=HEADERS, json=data)
    
    if res.status_code == 200:
        print("  ✅ Gist actualizado con el progreso de $44.")
        return True
    else:
        print(f"  ❌ Error actualizando Gist: {res.status_code}")
        return False

def publicar_en_foros():
    print(f"  📢 Compartiendo el Gist en foros con mensaje rotativo...")
    
    # Elegir un mensaje de apoyo al azar
    mensaje_apoyo = random.choice(CTAS)
    gist_url = f"https://gist.github.com/alfrexo95/{GIST_ID}"
    
    # Combinar el mensaje de apoyo con el enlace
    mensaje = f"🇨🇺 **Direct Relief for Cuban Families**\n\n{mensaje_apoyo}\n\nSee the evidence and donation addresses here:\n{gist_url}\n\n#Cuba #Bitcoin #Solidarity"
    
    # Crear un archivo temporal para los servicios que requieren subir un archivo
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
                if isinstance(payload, str):
                    res = requests.post(url, data=payload, timeout=15)
                else:
                    res = requests.post(url, data=payload, timeout=15)
                print(f"    - {url.split('/')[2]}: {res.status_code}")
                if res.status_code in [200, 201]:
                    exitos += 1
            elif method == "FILE":
                with open(temp_file, "rb") as f:
                    files = {payload: f}
                    res = requests.post(url, files=files, timeout=30)
                print(f"    - {url.split('/')[2]}: {res.status_code}")
                if res.status_code in [200, 201]:
                    exitos += 1
            elif method == "TELEGRAPH":
                acc_res = requests.post("https://api.telegra.ph/createAccount", json={"short_name": "CubaRelief", "author_name": "PredathorHaley"})
                if acc_res.status_code == 200:
                    token = acc_res.json()['result']['access_token']
                    payload['access_token'] = token
                    res = requests.post(url, json=payload, timeout=15)
                    print(f"    - telegra.ph: {res.status_code}")
                    if res.status_code == 200:
                        exitos += 1
        except Exception as e:
            print(f"    - Error en {url}: {e}")
    
    if os.path.exists(temp_file):
        os.remove(temp_file)
        
    print(f"  ✅ Compartido exitosamente en {exitos} plataformas.")

if __name__ == "__main__":
    actualizar_gist_progreso()
    publicar_en_foros()
