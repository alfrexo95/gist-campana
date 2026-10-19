import requests
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
GIST_URL = "https://gist.github.com/alfrexo95/4c1dea8f2b1ec60aff12af268b8e4a24"

def publicar_en_foros():
    print(f"  📢 Compartiendo el Gist estático: {GIST_URL}")
    print(f"  ⏰ Hora de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    mensaje = f"🇨🇺 **Direct Relief for Cuban Families**\n\nFamilies in Cuba are facing severe shortages of food and medicine. We use crypto to deliver aid directly. See the evidence and donation addresses here:\n\n{GIST_URL}\n\n#Cuba #Bitcoin #Solidarity"
    
    # Crear un archivo temporal para los servicios que requieren subir un archivo
    temp_file = "temp_message.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(mensaje)

    # Lista de servicios: (nombre, método, url, payload)
    foros = [
        # --- Foros existentes ---
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
        
        # --- Nuevos sitios investigados ---
        # Hastebin: espera el texto crudo (data)
        ("POST", "https://hastebin.com/documents", mensaje),
        # IX.io: espera un campo 'f' con el texto
        ("POST", "http://ix.io", {"f": mensaje}),
        # Fiche.rs: similar a otros pastebins
        ("POST", "https://fiche.rs", {"text": mensaje}),
        # Env.sh: requiere subir un archivo (multipart)
        ("FILE", "https://envs.sh", "file"),
        # 0x0.st: requiere subir un archivo (multipart)
        ("FILE", "https://0x0.st", "file"),
        # Paste.centos.org: endpoint /api/create con campo 'text'
        ("POST", "https://paste.centos.org/api/create", {"text": mensaje}),
        # Paste.debian.net: POST con campo 'text' o JSON
        ("POST", "https://paste.debian.net/", {"text": mensaje}),
    ]
    
    exitos = 0
    for method, url, payload in foros:
        try:
            if method == "POST":
                # Si el payload es un string, enviamos data, si es dict, enviamos data o json
                if isinstance(payload, str):
                    res = requests.post(url, data=payload, timeout=15)
                else:
                    res = requests.post(url, data=payload, timeout=15)
                print(f"    - {url.split('/')[2]}: {res.status_code}")
                if res.status_code in [200, 201]:
                    exitos += 1
            elif method == "FILE":
                # Para los servicios que requieren archivo
                with open(temp_file, "rb") as f:
                    files = {payload: f}
                    res = requests.post(url, files=files, timeout=30)
                print(f"    - {url.split('/')[2]}: {res.status_code}")
                if res.status_code in [200, 201]:
                    exitos += 1
            elif method == "TELEGRAPH":
                # Telegraph requiere crear una cuenta primero
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
    
    # Limpiar el archivo temporal
    if os.path.exists(temp_file):
        os.remove(temp_file)
        
    print(f"  ✅ Compartido exitosamente en {exitos} plataformas.")

if __name__ == "__main__":
    publicar_en_foros()
