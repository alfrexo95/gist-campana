import requests
from datetime import datetime

# --- CONFIGURACIÓN ---
# Aquí ponemos tu enlace estático del Gist
GIST_URL = "https://gist.github.com/alfrexo95/4c1dea8f2b1ec60aff12af268b8e4a24"

def publicar_en_foros():
    print(f"  📢 Compartiendo el Gist estático: {GIST_URL}")
    print(f"  ⏰ Hora de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    mensaje = f"🇨🇺 **Direct Relief for Cuban Families**\n\nFamilies in Cuba are facing severe shortages of food and medicine. We use crypto to deliver aid directly. See the evidence and donation addresses here:\n\n{GIST_URL}\n\n#Cuba #Bitcoin #Solidarity"
    
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
    ]
    
    exitos = 0
    for method, url, payload in foros:
        try:
            if method == "POST":
                res = requests.post(url, json=payload if isinstance(payload, dict) else None, data=payload if isinstance(payload, str) else None, timeout=15)
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
            
    print(f"  ✅ Compartido exitosamente en {exitos} plataformas.")

if __name__ == "__main__":
    publicar_en_foros()
