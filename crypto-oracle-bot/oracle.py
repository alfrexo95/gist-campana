import os, sys, requests, hashlib

ETH_ADDRESS       = os.environ.get("CRYPTO_ADDRESS_ETH", "")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")
GITHUB_TOKEN      = os.environ.get("GITHUB_TOKEN", "")
REPO              = os.environ.get("GITHUB_REPOSITORY", "")
ISSUE_NUMBER      = os.environ.get("ISSUE_NUMBER", "").strip()
ISSUE_USER        = os.environ.get("ISSUE_USER", "mystery_user")
COMMENT_BODY      = os.environ.get("COMMENT_BODY", "")
EVENT_NAME        = os.environ.get("EVENT_NAME", "")
TEST_ISSUE        = os.environ.get("TEST_ISSUE", "").strip()

def log(m): print(f"[ORACLE] {m}", flush=True)
log(f"Evento={EVENT_NAME} Repo={REPO} Issue={ISSUE_NUMBER!r} Token={bool(GITHUB_TOKEN)}")
log(f"Etherscan key: {'OK' if ETHERSCAN_API_KEY else 'FALTA'} | ETH addr: {ETH_ADDRESS[:10]}…")

if not GITHUB_TOKEN or not REPO:
    log("❌ Faltan GITHUB_TOKEN o GITHUB_REPOSITORY"); sys.exit(1)

headers = {"Authorization": f"token {GITHUB_TOKEN}",
           "Accept": "application/vnd.github.v3+json"}

def whoami():
    r = requests.get("https://api.github.com/user", headers=headers, timeout=20)
    log(f"Token es de: {r.json().get('login','?')} (HTTP {r.status_code})")

def post(text):
    if not ISSUE_NUMBER:
        log("❌ ISSUE_NUMBER vacío"); return
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"
    r = requests.post(url, headers=headers, json={"body": text}, timeout=20)
    log(f"POST comment → HTTP {r.status_code}")
    if r.status_code >= 400:
        log(f"❌ GitHub dijo: {r.text}")
    else:
        log(f"✅ Comentario: {r.json().get('html_url')}")

ART = {
"rocket": r"""
       /\
      /  \
     /    \
    /      \
   /        \
  /          \
 /            \
/              \
|   TO THE     |
|    MOON!     |
|______________|
     |      |
""",
"diamond": r"""
       /\
      /  \
     /    \
    /      \
   /   _   \
  /   / \   \
 /___/___\___\
 |  DIAMOND   |
 |   HANDS    |
 |____________|
""",
"moon": r"""
      _____
     /     \
    /       \
   |   HODL  |
   |         |
    \       /
     \_____/
       | |
       | |
     __|_|__
    |  BULL  |
    |________|
""",
"chart": r"""
     ^
    / \
   /   \    /
  /     \  /
 /       \/
 |       /\
 |      /  \
 |     /    \
 |____/______\
 |   TO THE   |
 |   MOON!    |
 |____________|
"""
}
JOKES = [
 "Why did Bitcoin go to therapy? Too many blocks in its past.",
 "Why did the trader break up with the chart? It kept showing red flags.",
 "What's a crypto investor's favorite dance? The HODL.",
 "Why don't Bitcoiners get lost? They always follow the whitepaper.",
]
ZEN = [
 "The market transfers money from the impatient to the patient. — Warren Buffett",
 "Be fearful when others are greedy, and greedy when others are fearful. — Warren Buffett",
 "In the middle of difficulty lies opportunity. — Albert Einstein",
 "Price is what you pay. Value is what you get. — Warren Buffett",
]

def reading(user, num, premium=False):
    r = int(hashlib.sha256(f"{user}-{num}".encode()).hexdigest(), 16)
    art = ART[list(ART)[r % len(ART)]]
    out = f"{art}\n\n💡 {JOKES[r % len(JOKES)]}\n\n🧘 {ZEN[r % len(ZEN)]}"
    if premium:
        out += ("\n\n🔮 **Premium Prophecy** 🔮\n"
                "• Stars align for strategic accumulation.\n"
                "• Watch weekly close above the 50-day MA.\n"
                "• Diamonds are forged under pressure.\n"
                "• Your conviction will be tested — hold steady.")
    return out

def verify_eth(tx_hash):
    if not ETHERSCAN_API_KEY:
        return False, "Etherscan API key no configurada."
    try:
        r = requests.get("https://api.etherscan.io/api", params={
            "module":"account","action":"txlist","address":ETH_ADDRESS,
            "sort":"desc","apikey":ETHERSCAN_API_KEY}, timeout=20).json()
    except Exception as e:
        return False, f"Error consultando Etherscan: {e}"
    if r.get("status") != "1":
        return False, f"Etherscan: {r.get('message','error')} — {r.get('result','')}"
    for tx in r["result"]:
        if tx["hash"].lower() == tx_hash.lower() and tx["to"].lower() == ETH_ADDRESS.lower():
            eth = int(tx["value"]) / 1e18
            usd = eth * 2000
            if usd >= 0.50:
                return True, f"{eth:.6f} ETH verificados (≈${usd:.2f})"
            return False, f"Monto insuficiente: {eth:.6f} ETH (≈${usd:.2f})"
    return False, "TX no encontrada para esta dirección."

if EVENT_NAME == "workflow_dispatch":
    log("=== TEST MANUAL ===")
    whoami()
    if TEST_ISSUE:
        ISSUE_NUMBER = TEST_ISSUE
        post(f"🧪 **Test del Oracle**\n\n{reading('test_user', TEST_ISSUE)}")
    else:
        log("✅ Diagnóstico OK. Sin TEST_ISSUE, no comento.")
    sys.exit(0)

if EVENT_NAME == "issues":
    msg = (f"🔮 **The GitHub Crypto Oracle** 🔮\n\n"
           f"Greetings **@{ISSUE_USER}**, spirits consulted for issue #{ISSUE_NUMBER}.\n\n"
           f"```text\n{reading(ISSUE_USER, ISSUE_NUMBER)}\n```\n\n"
           f"**Premium prophecy?** Send **$0.50 in ETH** to `{ETH_ADDRESS}` "
           f"and comment `/premium <tx_hash>`")
    post(msg)

elif EVENT_NAME == "issue_comment":
    body = COMMENT_BODY.strip()
    if body.startswith("/premium"):
        parts = body.split()
        if len(parts) < 2:
            post("❌ Uso: `/premium <tx_hash>`")
        else:
            ok, d = verify_eth(parts[1])
            log(f"verify → ok={ok} {d}")
            post((f"✅ **{d}**\n\n{reading(ISSUE_USER, ISSUE_NUMBER, True)}")
                 if ok else f"❌ **Pago no verificado:** {d}")
    else:
        post(f"🔮 *The Oracle whispers…*\n\n{reading(ISSUE_USER, ISSUE_NUMBER)}")
