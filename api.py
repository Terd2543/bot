"""
PHANTOM — Free Fire MITM Pro
Public IP version — รันบน VPS/VM จริงที่มี public IP
Python 3.11+  |  pip install mitmproxy flask
"""

import argparse, json, os, re, signal, sys, threading, time, random, socket
from pathlib import Path

# ─── third-party ─────────────────────────────────────────────────────────────
def _require(pkg: str, import_name: str | None = None):
    import importlib
    name = import_name or pkg
    try:
        return importlib.import_module(name)
    except ImportError:
        print(f"[phantom] missing: {pkg}  →  pip install {pkg}")
        sys.exit(1)

# ─── IP detection — public IP only ──────────────────────────────────────────
def get_public_ip() -> str:
    """
    ดึง public IP จริงจาก metadata server ของ cloud provider
    Oracle → GCP → AWS → fallback ipify
    timeout 3s ต่อ endpoint ไม่ hang
    """
    import urllib.request

    # Oracle Cloud metadata
    try:
        req = urllib.request.Request(
            "http://169.254.169.254/opc/v1/vnics/",
            headers={"Authorization": "Bearer Oracle"}
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
            if isinstance(data, list) and data:
                ip = data[0].get("publicIp")
                if ip:
                    return ip
    except Exception:
        pass

    # GCP metadata
    try:
        req = urllib.request.Request(
            "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/externalIp",
            headers={"Metadata-Flavor": "Google"}
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            ip = r.read().decode().strip()
            if ip:
                return ip
    except Exception:
        pass

    # AWS metadata
    try:
        # token ก่อน (IMDSv2)
        req_token = urllib.request.Request(
            "http://169.254.169.254/latest/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
        )
        with urllib.request.urlopen(req_token, timeout=3) as r:
            token = r.read().decode().strip()
        req_ip = urllib.request.Request(
            "http://169.254.169.254/latest/meta-data/public-ipv4",
            headers={"X-aws-ec2-metadata-token": token}
        )
        with urllib.request.urlopen(req_ip, timeout=3) as r:
            ip = r.read().decode().strip()
            if ip:
                return ip
    except Exception:
        pass

    # fallback — public IP services
    for url in [
        "https://api.ipify.org",
        "https://api64.ipify.org",
        "https://checkip.amazonaws.com",
        "https://icanhazip.com",
    ]:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                ip = r.read().decode().strip()
                if ip:
                    return ip
        except Exception:
            continue

    # last resort — LAN IP
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

# ─── paths & config ──────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "phantom_config.json"

DEFAULT_CONFIG: dict = {
    "proxy_host": "0.0.0.0",
    "proxy_port": 8080,
    "web_port":   8888,
    "features": {
        "esp_box":        False,
        "esp_skeleton":   False,
        "esp_distance":   False,
        "esp_health":     False,
        "esp_name":       False,
        "esp_loot":       False,
        "aimbot":         False,
        "aimbot_fov":     15,
        "aimbot_smooth":  5,
        "aimbot_bone":    "head",
        "skin_gun":       False,
        "skin_gun_id":    "0",
        "skin_char":      False,
        "skin_char_id":   "0",
        "no_recoil":      False,
        "speed_hack":     False,
        "speed_value":    1.0,
        "antiban_mode":   True,
    },
}

def load_cfg() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
    return json.loads(json.dumps(DEFAULT_CONFIG))

def save_cfg(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

_cfg_mtime = 0.0
_cfg_cache: dict = {}

def _live_cfg() -> dict:
    global _cfg_mtime, _cfg_cache
    try:
        mt = CONFIG_PATH.stat().st_mtime
        if mt != _cfg_mtime:
            _cfg_cache = json.loads(CONFIG_PATH.read_text())
            _cfg_mtime = mt
    except Exception:
        pass
    return _cfg_cache

def feat(key: str, default=False):
    return _live_cfg().get("features", {}).get(key, default)

def feat_val(key: str, default=0):
    return _live_cfg().get("features", {}).get(key, default)

# ═══════════════════════════════════════════════════════════════════════════════
# MITMPROXY ADDON
# ═══════════════════════════════════════════════════════════════════════════════

FF_ENDPOINTS = {
    "entity_state":  re.compile(r"garena\.com.*(entity|player|state|nearby)", re.I),
    "loadout":       re.compile(r"garena\.com.*(loadout|inventory|equip|skin)", re.I),
    "weapon_config": re.compile(r"garena\.com.*(weapon|gun|config|balance)", re.I),
    "char_config":   re.compile(r"garena\.com.*(character|char|avatar)", re.I),
    "match_config":  re.compile(r"garena\.com.*(match|room|session|game_config)", re.I),
    "movement":      re.compile(r"garena\.com.*(move|speed|physics|player_stat)", re.I),
}

class PhantomAddon:
    def request(self, flow):
        if feat("antiban_mode"):
            self._strip_fp(flow)

    def response(self, flow):
        url = flow.request.pretty_url
        for key, pat in FF_ENDPOINTS.items():
            if pat.search(url):
                h = getattr(self, f"_h_{key}", None)
                if h:
                    try:
                        h(flow)
                    except Exception:
                        pass
                break

    def _h_entity_state(self, flow):
        body = self._json(flow)
        if body is None:
            return
        need_esp = any(feat(k) for k in (
            "esp_box","esp_skeleton","esp_distance","esp_health","esp_name"))
        changed = False
        if need_esp:
            for e in self._entities(body):
                e["visible"] = True;  e["isVisible"] = True;  e["vis"] = 1
                if feat("esp_health"):
                    e.setdefault("hp",    e.get("health", 100))
                    e.setdefault("maxHp", e.get("maxHealth", 100))
                if feat("esp_distance"):
                    e.setdefault("dist",  e.get("distance", 0))
                if feat("esp_name"):
                    e.setdefault("name",  e.get("nickname", "PLAYER"))
                changed = True
        if feat("esp_loot"):
            for item in self._extract(body, ("loot","items","drops","lootList")):
                item["visible"] = True;  item["showLoot"] = True
                changed = True
        if changed:
            self._put(flow, body)

    def _h_match_config(self, flow):
        body = self._json(flow)
        if body is None or not feat("aimbot"):
            return
        fov    = float(feat_val("aimbot_fov",    15))
        smooth = float(feat_val("aimbot_smooth",  5))
        bone   = str (feat_val("aimbot_bone",  "head"))
        blk = body.get("gameConfig", body.get("config", body))
        if isinstance(blk, dict):
            blk["aimAssistFov"]      = fov
            blk["aimAssistStrength"] = max(0.0, 1.0 - smooth / 10.0)
            blk["aimAssistBone"]     = bone
            blk["aimAssistEnabled"]  = True
            body["gameConfig"] = blk
        self._put(flow, body)

    def _h_weapon_config(self, flow):
        body = self._json(flow)
        if body is None or not feat("no_recoil"):
            return
        changed = False
        for w in self._extract(body, ("weapons","weaponList","guns","data")):
            w["recoilVertical"]   = 0
            w["recoilHorizontal"] = 0
            w["bulletSpread"]     = 0
            w["recoilRecover"]    = 9999
            changed = True
        if changed:
            self._put(flow, body)

    def _h_loadout(self, flow):
        body = self._json(flow)
        if body is None or not feat("skin_gun"):
            return
        gid = str(feat_val("skin_gun_id", "0"))
        changed = False
        for s in self._extract(body, ("loadout","slots","inventory","equip","data")):
            if "gunSkin" in s or "weaponSkin" in s:
                s["gunSkin"] = gid;  s["weaponSkin"] = gid
                changed = True
        if changed:
            self._put(flow, body)

    def _h_char_config(self, flow):
        body = self._json(flow)
        if body is None or not feat("skin_char"):
            return
        cid = str(feat_val("skin_char_id", "0"))
        for k in ("characterId","charId","avatarId","skinId"):
            if isinstance(body, dict) and k in body:
                body[k] = cid
        self._put(flow, body)

    def _h_movement(self, flow):
        body = self._json(flow)
        if body is None or not feat("speed_hack"):
            return
        spd = max(0.5, min(float(feat_val("speed_value", 1.0)), 3.0))
        for k in ("moveSpeed","walkSpeed","runSpeed","speedMultiplier"):
            if isinstance(body, dict) and k in body:
                body[k] = body[k] * spd
        self._put(flow, body)

    def _strip_fp(self, flow):
        for h in ("x-gameloft-fingerprint","x-garena-fp","x-device-id","x-install-id"):
            if h in flow.request.headers:
                del flow.request.headers[h]
        time.sleep(random.uniform(0.001, 0.008))

    def _json(self, flow):
        ct = flow.response.headers.get("content-type", "")
        if "json" not in ct:
            return None
        try:
            return json.loads(flow.response.content)
        except Exception:
            return None

    def _put(self, flow, body):
        flow.response.content = json.dumps(body, separators=(",",":")).encode()
        flow.response.headers["content-type"] = "application/json"
        flow.response.headers.pop("content-length", None)

    def _entities(self, body) -> list:
        return self._extract(body, ("entities","players","nearbyPlayers","entityList","data"))

    def _extract(self, body, keys: tuple) -> list:
        for k in keys:
            if isinstance(body, dict) and k in body:
                v = body[k]
                if isinstance(v, list):
                    return v
        return body if isinstance(body, list) else []

addons = [PhantomAddon()]

# ═══════════════════════════════════════════════════════════════════════════════
# FLASK PANEL — same as before
# ═══════════════════════════════════════════════════════════════════════════════

PANEL_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>PHANTOM</title>
<style>
:root{
  --bg:#07070a;--sur:#101016;--card:#13131a;--bdr:#1e1e2a;
  --acc:#5555dd;--grn:#33cc66;--red:#cc3333;
  --txt:#c8c8e0;--mut:#44445a;--mono:"Courier New",monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:var(--mono);font-size:13px;min-height:100vh}
.hdr{background:var(--sur);border-bottom:1px solid var(--bdr);
     padding:14px 24px;display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:10}
.hdr h1{font-size:18px;letter-spacing:4px;color:#e0e0f0}
.hdr .sub{color:var(--mut);font-size:11px}
.hdr .status{margin-left:auto;font-size:11px;display:flex;align-items:center;gap:8px}
.dot{width:8px;height:8px;border-radius:50%;background:var(--grn);
     box-shadow:0 0 6px var(--grn);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.save-btn{background:var(--acc);border:none;color:#fff;
          padding:8px 22px;border-radius:5px;font-family:var(--mono);
          font-size:12px;cursor:pointer;letter-spacing:1px;
          transition:opacity .15s;margin-left:16px}
.save-btn:hover{opacity:.8}
.toast{position:fixed;bottom:24px;right:24px;background:var(--grn);color:#000;
       padding:10px 20px;border-radius:6px;font-size:12px;opacity:0;
       transition:opacity .3s;pointer-events:none;z-index:999}
.toast.show{opacity:1}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
      gap:14px;padding:20px 24px;max-width:1100px}
.card{background:var(--card);border:1px solid var(--bdr);border-radius:10px;padding:16px}
.card-title{font-size:10px;letter-spacing:2px;color:var(--mut);
            margin-bottom:14px;text-transform:uppercase}
.row{display:flex;align-items:center;justify-content:space-between;
     padding:7px 0;border-bottom:1px solid var(--bdr)}
.row:last-child{border-bottom:none}
.row label{color:var(--txt);font-size:12px;cursor:pointer;user-select:none}
.toggle{position:relative;display:inline-block;width:40px;height:22px}
.toggle input{opacity:0;width:0;height:0}
.slider{position:absolute;inset:0;background:#1a1a2a;border-radius:22px;
        border:1px solid var(--bdr);transition:background .2s;cursor:pointer}
.slider::before{content:"";position:absolute;width:14px;height:14px;
                left:3px;top:3px;background:var(--mut);border-radius:50%;
                transition:transform .2s,background .2s}
.toggle input:checked+.slider{background:#1a3a2a;border-color:#2a5a3a}
.toggle input:checked+.slider::before{transform:translateX(18px);background:var(--grn)}
.sub-row{display:flex;align-items:center;gap:10px;padding:6px 0;
         border-bottom:1px solid var(--bdr)}
.sub-row:last-child{border-bottom:none}
.sub-row .lbl{color:var(--mut);font-size:11px;min-width:88px}
input[type=range]{flex:1;accent-color:var(--acc);background:transparent}
.val{color:var(--grn);font-size:11px;min-width:32px;text-align:right}
input[type=text],input[type=number],select{
  background:var(--sur);border:1px solid var(--bdr);color:var(--txt);
  font-family:var(--mono);font-size:11px;padding:4px 8px;
  border-radius:4px;width:90px}
select option{background:var(--sur)}
.mcfg{background:var(--card);border:1px solid var(--bdr);border-radius:10px;
      padding:16px;grid-column:1/-1}
.copy-btn{background:#1a1a2a;border:1px solid var(--bdr);color:#8888cc;
          font-family:var(--mono);font-size:11px;padding:6px 14px;
          border-radius:4px;cursor:pointer;display:block}
.copy-btn:hover{border-color:var(--acc);color:var(--acc)}
.setup-step{display:flex;align-items:flex-start;gap:10px;
            font-size:11px;color:var(--txt);line-height:1.6}
.step-num{background:var(--acc);color:#fff;border-radius:50%;
          width:18px;height:18px;display:flex;align-items:center;
          justify-content:center;font-size:10px;flex-shrink:0;margin-top:1px}
.proxy-box,.cert-box{background:var(--sur);border:1px solid var(--bdr);
                     border-radius:6px;padding:10px 14px;margin-top:8px}
.prow{display:flex;gap:16px;padding:3px 0}
.plbl{color:var(--mut);font-size:11px;min-width:50px}
.pval{color:var(--grn);font-size:11px;font-weight:bold;font-family:var(--mono)}
.cert-box code{color:#8888cc;font-size:11px;word-break:break-all;display:block}
</style>
</head>
<body>
<div class="hdr">
  <h1>PHANTOM</h1>
  <span class="sub">feature panel</span>
  <div class="status"><span class="dot"></span><span>PROXY RUNNING</span></div>
  <button class="save-btn" onclick="saveAll()">SAVE &amp; APPLY</button>
</div>
<div class="grid">
  <div class="card">
    <div class="card-title">ESP</div>
    <div class="row"><label for="esp_box">Box ESP</label>
      <label class="toggle"><input type="checkbox" id="esp_box"><span class="slider"></span></label></div>
    <div class="row"><label for="esp_skeleton">Skeleton ESP</label>
      <label class="toggle"><input type="checkbox" id="esp_skeleton"><span class="slider"></span></label></div>
    <div class="row"><label for="esp_distance">Distance ESP</label>
      <label class="toggle"><input type="checkbox" id="esp_distance"><span class="slider"></span></label></div>
    <div class="row"><label for="esp_health">Health Bar</label>
      <label class="toggle"><input type="checkbox" id="esp_health"><span class="slider"></span></label></div>
    <div class="row"><label for="esp_name">Name ESP</label>
      <label class="toggle"><input type="checkbox" id="esp_name"><span class="slider"></span></label></div>
    <div class="row"><label for="esp_loot">Loot ESP</label>
      <label class="toggle"><input type="checkbox" id="esp_loot"><span class="slider"></span></label></div>
  </div>
  <div class="card">
    <div class="card-title">AIMBOT</div>
    <div class="row"><label for="aimbot">Enable Aimbot</label>
      <label class="toggle"><input type="checkbox" id="aimbot"><span class="slider"></span></label></div>
    <div class="sub-row">
      <span class="lbl">FOV</span>
      <input type="range" id="aimbot_fov" min="1" max="90" value="15"
             oninput="document.getElementById('v_aimbot_fov').textContent=this.value">
      <span class="val" id="v_aimbot_fov">15</span>
    </div>
    <div class="sub-row">
      <span class="lbl">Smooth</span>
      <input type="range" id="aimbot_smooth" min="1" max="10" value="5"
             oninput="document.getElementById('v_aimbot_smooth').textContent=this.value">
      <span class="val" id="v_aimbot_smooth">5</span>
    </div>
    <div class="sub-row">
      <span class="lbl">Bone</span>
      <select id="aimbot_bone">
        <option value="head">Head</option>
        <option value="neck">Neck</option>
        <option value="chest">Chest</option>
        <option value="stomach">Stomach</option>
      </select>
    </div>
    <div class="row" style="margin-top:8px"><label for="no_recoil">No Recoil</label>
      <label class="toggle"><input type="checkbox" id="no_recoil"><span class="slider"></span></label></div>
  </div>
  <div class="card">
    <div class="card-title">SKIN MOD</div>
    <div class="row"><label for="skin_gun">Gun Skin</label>
      <label class="toggle"><input type="checkbox" id="skin_gun"><span class="slider"></span></label></div>
    <div class="sub-row">
      <span class="lbl">Gun Skin ID</span>
      <input type="text" id="skin_gun_id" value="0" placeholder="skin ID">
    </div>
    <div class="row" style="margin-top:8px"><label for="skin_char">Character Skin</label>
      <label class="toggle"><input type="checkbox" id="skin_char"><span class="slider"></span></label></div>
    <div class="sub-row">
      <span class="lbl">Char Skin ID</span>
      <input type="text" id="skin_char_id" value="0" placeholder="char ID">
    </div>
  </div>
  <div class="card">
    <div class="card-title">MOVEMENT</div>
    <div class="row"><label for="speed_hack">Speed Hack</label>
      <label class="toggle"><input type="checkbox" id="speed_hack"><span class="slider"></span></label></div>
    <div class="sub-row">
      <span class="lbl">Speed ×</span>
      <input type="range" id="speed_value" min="0.5" max="3.0" step="0.1" value="1.0"
             oninput="document.getElementById('v_speed').textContent=parseFloat(this.value).toFixed(1)">
      <span class="val" id="v_speed">1.0</span>
    </div>
    <div class="row" style="margin-top:8px"><label for="antiban_mode">Anti-Ban</label>
      <label class="toggle"><input type="checkbox" id="antiban_mode"><span class="slider"></span></label></div>
  </div>
  <div class="card mcfg">
    <div class="card-title">iOS SETUP</div>
    <div id="setup-loading" style="color:var(--mut);font-size:11px">loading...</div>
    <div id="setup-body" style="display:none">
      <div class="setup-step"><span class="step-num">1</span>
        <span>iPhone → WiFi → (i) → Configure Proxy → Manual</span></div>
      <div class="proxy-box">
        <div class="prow"><span class="plbl">Server</span><span class="pval" id="s-ip">—</span></div>
        <div class="prow"><span class="plbl">Port</span><span class="pval" id="s-port">—</span></div>
      </div>
      <div class="setup-step" style="margin-top:14px"><span class="step-num">2</span>
        <span>Safari → URL ด้านล่าง → Allow → Settings → install → Trust</span></div>
      <div class="cert-box">
        <code id="cert-url">—</code>
        <button class="copy-btn" onclick="copyCertUrl()" style="margin-top:6px">copy URL</button>
      </div>
      <div id="cert-status" style="font-size:11px;margin-top:6px;color:var(--mut)">checking...</div>
      <div class="setup-step" style="margin-top:14px"><span class="step-num">3</span>
        <span>Settings → General → VPN &amp; Device Management → PHANTOM CA → Trust</span></div>
      <div class="setup-step" style="margin-top:14px"><span class="step-num">4</span>
        <span>เปิด Free Fire ✓</span></div>
    </div>
  </div>
</div>
<div class="toast" id="toast">Saved ✓</div>
<script>
const BOOLS  = ["esp_box","esp_skeleton","esp_distance","esp_health","esp_name",
                "esp_loot","aimbot","no_recoil","skin_gun","skin_char","speed_hack","antiban_mode"];
const RANGES = ["aimbot_fov","aimbot_smooth","speed_value"];
const TEXTS  = ["skin_gun_id","skin_char_id","aimbot_bone"];
async function loadConfig(){
  const r=(await fetch("/api/config")).json? await (await fetch("/api/config")).json():{};
  const f=r.features||{};
  BOOLS.forEach(k=>{const e=document.getElementById(k);if(e)e.checked=!!f[k]});
  RANGES.forEach(k=>{const e=document.getElementById(k);if(!e)return;e.value=f[k]??e.value;
    const v=document.getElementById("v_"+k);if(v)v.textContent=k==="speed_value"?parseFloat(e.value).toFixed(1):e.value});
  TEXTS.forEach(k=>{const e=document.getElementById(k);if(e)e.value=f[k]??e.value});
}
async function saveAll(){
  const features={};
  BOOLS.forEach(k=>{const e=document.getElementById(k);if(e)features[k]=e.checked});
  RANGES.forEach(k=>{const e=document.getElementById(k);if(e)features[k]=parseFloat(e.value)});
  TEXTS.forEach(k=>{const e=document.getElementById(k);if(e)features[k]=e.value});
  await fetch("/api/config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({features})});
  const t=document.getElementById("toast");t.classList.add("show");setTimeout(()=>t.classList.remove("show"),2000);
}
async function loadSetup(){
  try{
    const d=await(await fetch("/api/setup")).json();
    document.getElementById("s-ip").textContent=d.ip;
    document.getElementById("s-port").textContent=d.proxy_port;
    document.getElementById("cert-url").textContent=d.cert_url;
    const cs=document.getElementById("cert-status");
    if(d.cert_ready){cs.textContent="✓ cert ready";cs.style.color="var(--grn)"}
    else{cs.textContent="✗ cert not found — start proxy first";cs.style.color="var(--red)"}
    document.getElementById("setup-loading").style.display="none";
    document.getElementById("setup-body").style.display="block";
  }catch(e){document.getElementById("setup-loading").textContent="could not load setup info";}
}
function copyCertUrl(){
  navigator.clipboard.writeText(document.getElementById("cert-url").textContent).then(()=>{
    const t=document.getElementById("toast");t.textContent="copied ✓";t.classList.add("show");
    setTimeout(()=>{t.classList.remove("show");t.textContent="Saved ✓"},2000);
  });
}
loadConfig();loadSetup();
</script>
</body>
</html>"""

def _find_mitm_cert() -> Path | None:
    candidates = [
        Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem",
        Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.cer",
        Path("/root/.mitmproxy/mitmproxy-ca-cert.pem"),
        Path("/home/user/.mitmproxy/mitmproxy-ca-cert.pem"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def _build_mobileconfig(cert_b64: str, ip: str, proxy_port: int) -> str:
    import uuid
    pu = str(uuid.uuid4()).upper()
    cu = str(uuid.uuid4()).upper()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>PayloadContent</key><array><dict>
    <key>PayloadType</key><string>com.apple.security.root</string>
    <key>PayloadVersion</key><integer>1</integer>
    <key>PayloadIdentifier</key><string>lol.ph4nt0m.cert.{cu[:8].lower()}</string>
    <key>PayloadUUID</key><string>{cu}</string>
    <key>PayloadDisplayName</key><string>PHANTOM CA</string>
    <key>PayloadContent</key><data>{cert_b64}</data>
  </dict></array>
  <key>PayloadDisplayName</key><string>PHANTOM Cert — {ip}:{proxy_port}</string>
  <key>PayloadIdentifier</key><string>lol.ph4nt0m.profile.{pu[:8].lower()}</string>
  <key>PayloadUUID</key><string>{pu}</string>
  <key>PayloadType</key><string>Configuration</string>
  <key>PayloadVersion</key><integer>1</integer>
</dict></plist>"""

def run_flask(web_port: int, proxy_port: int, public_ip: str):
    _require("flask")
    from flask import Flask, request, jsonify, Response
    import base64, logging
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    app = Flask("phantom")

    @app.get("/api/config")
    def get_cfg(): return jsonify(load_cfg())

    @app.post("/api/config")
    def set_cfg():
        data = request.get_json(force=True, silent=True)
        if not data: return jsonify({"error":"bad json"}), 400
        cfg = load_cfg()
        cfg.setdefault("features", {}).update(data.get("features", {}))
        save_cfg(cfg)
        return jsonify({"ok": True})

    @app.get("/api/setup")
    def setup_info():
        cert_path = _find_mitm_cert()
        return jsonify({
            "ip":         public_ip,
            "proxy_port": proxy_port,
            "web_port":   web_port,
            "cert_url":   f"http://{public_ip}:{web_port}/cert",
            "cert_ready": cert_path is not None,
        })

    @app.get("/cert")
    def serve_cert():
        cert_path = _find_mitm_cert()
        if cert_path is None:
            return Response("cert not found — start proxy first", status=404, mimetype="text/plain")
        raw = cert_path.read_bytes()
        if b"BEGIN CERTIFICATE" in raw:
            b64 = "".join(l for l in raw.decode().splitlines() if not l.startswith("-----"))
        else:
            b64 = base64.b64encode(raw).decode()
        return Response(
            _build_mobileconfig(b64, public_ip, proxy_port),
            mimetype="application/x-apple-aspen-config",
            headers={"Content-Disposition": "attachment; filename=phantom.mobileconfig"}
        )

    @app.get("/")
    def panel(): return Response(PANEL_HTML, mimetype="text/html")

    app.run(host="0.0.0.0", port=web_port, debug=False, use_reloader=False)

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="PHANTOM — Free Fire MITM")
    parser.add_argument("--proxy-port", type=int, default=8080)
    parser.add_argument("--proxy-host", type=str, default="0.0.0.0")
    parser.add_argument("--web-port",   type=int, default=8888)
    parser.add_argument("--web-only",   action="store_true")
    args = parser.parse_args()

    cfg = load_cfg()
    cfg["proxy_host"] = args.proxy_host
    cfg["proxy_port"] = args.proxy_port
    cfg["web_port"]   = args.web_port
    save_cfg(cfg)

    print("[phantom] detecting public IP...")
    public_ip = get_public_ip()

    threading.Thread(
        target=run_flask,
        args=(args.web_port, args.proxy_port, public_ip),
        daemon=True
    ).start()

    print(f"""
╔══════════════════════════════════════════════════╗
║              PHANTOM  by NULLDASH                ║
╠══════════════════════════════════════════════════╣
║  proxy   →  {public_ip}:{args.proxy_port:<32}║
║  panel   →  http://{public_ip}:{args.web_port:<24}║
║  cert    →  http://{public_ip}:{args.web_port}/cert{'':<18}║
╚══════════════════════════════════════════════════╝

iPhone setup:
  1. WiFi → Configure Proxy → Manual
     Server : {public_ip}
     Port   : {args.proxy_port}
  2. Safari → http://{public_ip}:{args.web_port}/cert → Trust
  3. เปิด Free Fire ✓
""")

    if args.web_only:
        try:
            signal.pause()
        except AttributeError:
            threading.Event().wait()
        return

    _require("mitmproxy", "mitmproxy")
    from mitmproxy.tools import main as mitm_main
    sys.argv = [
        "mitmproxy",
        "--listen-host", args.proxy_host,
        "--listen-port", str(args.proxy_port),
        "-s", __file__,
        "--mode", "regular",
        "--ssl-insecure",
        "--quiet",
    ]
    try:
        mitm_main.mitmdump()
    except KeyboardInterrupt:
        print("\n[phantom] stopped.")

if __name__ == "__main__":
    main()
