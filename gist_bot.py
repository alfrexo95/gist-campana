import os, requests, json, random, time

PAT_TOKEN = os.environ.get("PAT_TOKEN")
REPO_NAME = "alfrexo95/FondosAngor"
STATE_FILE = "gist_state.json"
HEADERS = {"Authorization": f"token {PAT_TOKEN}", "Accept": "application/vnd.github.v3+json"}

PAYMENT_ADDRESSES = """
₿ **BTC:** `bc1qt3rukpe7qp737zj5j5xpxxmcqv90cfefhg5e00`
Ξ **ETH:** `0xA5E6eB31868A85127B1ED82b8C760193356206ED`
Ł **LTC:** `ltc1qdyyg99l8ehp9aj4ehzvmefglmpl9750226k7ne`
⚡ **Lightning:** `chieftrait089@walletofsatoshi.com`
"""

GIST_FILENAME = "Cuba_Relief_Campaign.md"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"gist_id": None, "media_index": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# --- NUEVOS SERVICIOS DE ALOJAMIENTO ---
def upload_image_image2url(filepath):
    """Sube imágenes a Image2URL (límite 2MB)."""
    print(f"  ☁️ Subiendo {os.path.basename(filepath)} a Image2URL...")
    try:
        with open(filepath, "rb") as f:
            res = requests.post("https://www.image2url.com/api/upload", files={"file": f}, timeout=60)
        if res.status_code == 200:
            return res.json().get("url")
    except Exception as e:
        print(f"  ❌ Error subiendo a Image2URL: {e}")
    return None

def upload_video_brewpage(filepath):
    """Sube videos a BrewPage (límite 20MB)."""
    print(f"  ☁️ Subiendo {os.path.basename(filepath)} a BrewPage...")
    try:
        with open(filepath, "rb") as f:
            res = requests.post("https://brewpage.app/api/files?ns=public", files={"file": f}, timeout=120)
        if res.status_code in [200, 201]:
            data = res.json()
            # BrewPage devuelve una URL directa
            return data.get("url")
    except Exception as e:
        print(f"  ❌ Error subiendo a BrewPage: {e}")
    return None

def obtener_media(state):
    """Obtiene un archivo del repo privado y lo sube a un host público compatible."""
    print("  🔍 Buscando evidencias en FondosAngor...")
    api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/media"
    res = requests.get(api_url, headers=HEADERS, timeout=15)
    
    if res.status_code != 200:
        print(f"  ⚠️ No se pudo acceder a la carpeta media (Error {res.status_code}).")
        return ""
        
    files = [f for f in res.json() if f['name'].lower().endswith(('.jpg', '.jpeg', '.png', '.mp4'))]
    if not files:
        return ""
        
    files = sorted(files, key=lambda x: x['name'])
    idx = state.get("media_index", 0) % len(files)
    selected = files[idx]
    
    download_url = selected['download_url']
    r = requests.get(download_url, headers=HEADERS, timeout=30)
    temp_file = f"/tmp/{selected['name']}"
    with open(temp_file, 'wb') as f:
        f.write(r.content)
        
    # Elegir el servicio según el tipo de archivo
    public_url = None
    if selected['name'].lower().endswith('.mp4'):
        public_url = upload_video_brewpage(temp_file)
    else:
        public_url = upload_image_image2url(temp_file)
        
    os.remove(temp_file)
    state["media_index"] = idx + 1
    
    if not public_url:
        return ""
        
    print(f"  ✅ Evidencia pública lista: {selected['name']}")
    if selected['name'].lower().endswith('.mp4'):
        return f"\n🎥 **[Watch Video Evidence Here]({public_url})**\n"
    else:
        return f"\n![Evidence Image]({public_url})\n"

# --- PUBLICACIÓN EN 10 FOROS ---
def publicar_en_foros(gist_url):
    print("  📢 Publicando enlace del Gist en 10 foros y plataformas...")
    mensaje = f"🇨🇺 **Direct Relief for Cuban Families**\n\nFamilies in Cuba are facing severe shortages of food and medicine. We use crypto to deliver aid directly. See the evidence and donation addresses here:\n\n{gist_url}\n\n#Cuba #Bitcoin #Solidarity"
    
    # Lista de endpoints (método, url, payload)
    foros = [
        ("POST", "https://free.intcount.com/api/botchan/post", {"content": mensaje, "tag": "meta"}),
        ("POST", "https://anystation.net/", {"content": mensaje}),
        ("POST", "https://paste.rs/", mensaje),
        ("POST", "https://dpaste.com/api/v2/", {"content": mensaje}),
        ("POST", "https://snippet.host/", {"content": mensaje}),
        ("POST", "https://paste.c-net.org/", mensaje),
        ("POST", "https://pastebin.ai/api/v1/paste", {"content": mensaje}),
        ("POST", "https://brewpage.app/api/html?format=markdown", {"content": mensaje}),
        # Telegraph requiere un método especial (se maneja aparte)
        ("TELEGRAPH", "https://api.telegra.ph/createPage", {"title": "Cuba Relief", "content": mensaje}),
        # Termbin usa netcat, pero podemos usar su API HTTP
        ("POST", "https://termbin.com/", mensaje),
    ]
    
    for method, url, payload in foros:
        try:
            if method == "POST":
                res = requests.post(url, json=payload if isinstance(payload, dict) else None, data=payload if isinstance(payload, str) else None, timeout=15)
                print(f"    - {url.split('/')[2]}: {res.status_code}")
            elif method == "TELEGRAPH":
                # Telegraph requiere un token de acceso; creamos uno automáticamente
                acc_res = requests.post("https://api.telegra.ph/createAccount", json={"short_name": "CubaRelief", "author_name": "PredathorHaley"})
                if acc_res.status_code == 200:
                    token = acc_res.json()['result']['access_token']
                    payload['access_token'] = token
                    res = requests.post(url, json=payload, timeout=15)
                    print(f"    - telegra.ph: {res.status_code}")
        except Exception as e:
            print(f"    - Error en {url}: {e}")
    print("  ✅ Proceso de publicación en foros finalizado.")

def crear_o_actualizar_gist(state, contenido_md):
    gist_data = {
        "description": "🚨 Direct Relief for Cuban Families - Crypto Donations Accepted",
        "public": True,
        "files": {GIST_FILENAME: {"content": contenido_md}}
    }

    if not state.get("gist_id"):
        print("  📝 Creando nuevo Gist público...")
        res = requests.post("https://api.github.com/gists", headers=HEADERS, json=gist_data, timeout=15)
        if res.status_code == 201:
            gist_id = res.json()['id']
            print(f"  ✅ Gist creado: {res.json()['html_url']}")
            return gist_id, res.json()['html_url']
    else:
        print("  🔄 Actualizando Gist existente...")
        url = f"https://api.github.com/gists/{state['gist_id']}"
        res = requests.patch(url, headers=HEADERS, json=gist_data, timeout=15)
        if res.status_code == 200:
            print(f"  ✅ Gist actualizado: {res.json()['html_url']}")
            return state["gist_id"], res.json()['html_url']
            
    return state.get("gist_id"), None

def main():
    state = load_state()
    media_md = obtener_media(state)
    
    contenido = f"""# 🇨🇺 Direct Relief for Cuban Families

**The economic crisis in Cuba is pushing vulnerable families to the brink.** Famine and lack of medicine are daily realities.

**The Reality on the Ground:**
Families are struggling to find basic food items. Children are going to bed hungry. Hospitals lack essential medicines and supplies. The blockade makes traditional international transfers almost impossible, cutting off many sources of aid.

**Why Crypto?**
We use decentralized technology (Bitcoin, Lightning, and other cryptocurrencies) to bypass these barriers. This creates a direct, peer-to-peer channel to deliver food, medical supplies, and dignity directly to those in need. No banks, no middlemen, no censorship.

**How You Can Help:**
Every sat and every fraction of a coin helps. Please use the following official addresses:

{PAYMENT_ADDRESSES}

---
## 📸 Related Photos and Videos
{media_md}
---
*Transparency is key. We document everything. Updated automatically every 8 hours.*
*Created by [PredathorHaley](https://github.com/alfrexo95)*
"""

    gist_id, gist_url = crear_o_actualizar_gist(state, contenido)
    if gist_id:
        state["gist_id"] = gist_id
        save_state(state)
        if gist_url:
            publicar_en_foros(gist_url)

if __name__ == "__main__":
    main()
