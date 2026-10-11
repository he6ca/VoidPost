"""
VOID//POST - single-file web GUI + Python backend for posting to a
Facebook Page you manage, via Facebook's official Graph API.

Run:
    pip install flask requests
    python voidpost.py

Then open http://127.0.0.1:5000 in your browser.

Talks ONLY to Facebook's official Graph API using a token you provide.
Page posting only, as Facebook's platform rules require.
"""

import html as htmllib
import json
import os

import requests
from flask import Flask, Response, jsonify, request

app = Flask(__name__)

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".fb_poster_gui_config.json")
GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
MAX_POSTS = 10


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)


def graph_message(resp, fallback):
    try:
        return resp.json().get("error", {}).get("message", fallback)
    except Exception:
        return fallback


# ---------------------------------------------------------------------------
# Front-end (HTML / CSS / JS), styled after VOID//SEARCH
# ---------------------------------------------------------------------------
PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VOID//POST</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow+Condensed:wght@400;600;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#000; --panel:#0a0a0a; --card:#111; --field:#0d0d0d;
  --border:#1f1f1f; --border2:#2a2a2a;
  --red:#b91c1c; --red2:#ef4444; --red3:#fca5a5;
  --dim:#666; --muted:#333; --text:#888; --bright:#ccc; --white:#eee;
  --ok:#22c55e; --warn:#f59e0b;
  --fh:'Bebas Neue',sans-serif;
  --fb:'Barlow Condensed',sans-serif;
  --fm:'Share Tech Mono',monospace;
}
*{margin:0;padding:0;box-sizing:border-box;}
[hidden]{display:none !important;}
html{scroll-behavior:smooth;}
body{background:var(--bg);color:var(--text);font-family:var(--fb);min-height:100vh;overflow-x:hidden;}

/* scanlines + grain */
body::before{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:999;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.15) 2px,rgba(0,0,0,.15) 4px);
}
body::after{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:998;opacity:.6;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
}

.wrap{max-width:900px;margin:0 auto;padding:0 18px 80px;position:relative;z-index:2;}

/* topbar */
.topbar{display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-bottom:1px solid var(--border);}
.tbl{font-family:var(--fm);font-size:10px;letter-spacing:4px;color:var(--muted);text-transform:uppercase;}
.tbl span{color:var(--red2);}
.status{display:flex;align-items:center;gap:8px;font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--text);}
.dot{width:8px;height:8px;border-radius:50%;background:var(--muted);}
.dot.ok{background:var(--ok);box-shadow:0 0 8px var(--ok);}
.dot.err{background:var(--red2);box-shadow:0 0 8px var(--red2);}
.dot.busy{background:var(--warn);box-shadow:0 0 8px var(--warn);animation:blink 1s steps(2) infinite;}
@keyframes blink{50%{opacity:.25;}}

/* masthead */
.masthead{position:relative;overflow:hidden;padding:26px 0 18px;border-bottom:3px solid var(--red);}
.masthead::before{
  content:'VOID//POST';position:absolute;font-family:var(--fh);
  font-size:clamp(7rem,16vw,14rem);color:rgba(185,28,28,.05);
  top:50%;left:-8px;transform:translateY(-50%);letter-spacing:-6px;white-space:nowrap;pointer-events:none;
}
.logo{position:relative;font-family:var(--fh);font-size:clamp(3.4rem,11vw,7.5rem);line-height:.9;letter-spacing:4px;color:var(--white);}
.logo .slash{color:var(--red);}
.logo .ver{font-family:var(--fm);font-size:clamp(.8rem,2vw,1.2rem);color:var(--red2);vertical-align:super;letter-spacing:3px;margin-left:8px;}
.sub{position:relative;font-family:var(--fm);font-size:10px;letter-spacing:5px;color:var(--dim);text-transform:uppercase;margin-top:10px;}

/* tabs */
.tabs{display:flex;border-bottom:1px solid var(--border);margin-top:18px;}
.tab{
  flex:1;background:transparent;border:none;border-bottom:2px solid transparent;
  padding:12px 6px;font-family:var(--fm);font-size:11px;letter-spacing:3px;
  color:#666;text-transform:uppercase;cursor:pointer;transition:color .2s,border-color .2s,background .2s;
}
.tab:hover{color:#ddd;background:rgba(185,28,28,.05);}
.tab.on{color:var(--red2);border-bottom-color:var(--red);background:rgba(139,0,0,.08);}
.tab .n{color:var(--muted);margin-right:6px;}
.tab.on .n{color:var(--red);}

/* panels */
.panel{background:var(--panel);border:1px solid var(--border);border-top:none;padding:22px 20px;}
.panel-head{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:18px;gap:12px;flex-wrap:wrap;}
.sec-num{font-family:var(--fm);font-size:10px;color:var(--red2);letter-spacing:2px;}
.sec-title{font-family:var(--fh);font-size:26px;letter-spacing:2px;color:var(--bright);line-height:1;}

label.lbl{display:block;font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--text);text-transform:uppercase;margin-bottom:6px;}
input[type=text],input[type=password],input[type=number],textarea{
  width:100%;background:var(--field);border:1px solid var(--border2);border-radius:0;
  color:var(--white);padding:10px 12px;font-family:var(--fb);font-size:16px;outline:none;
  transition:border-color .15s,box-shadow .15s;
}
input:focus,textarea:focus{border-color:var(--red2);box-shadow:0 0 0 1px rgba(239,68,68,.25);}
textarea{resize:vertical;min-height:90px;line-height:1.4;}
.field{margin-bottom:16px;}
.row{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
@media (max-width:640px){.row{grid-template-columns:1fr;}}

.btn{
  font-family:var(--fm);font-size:11px;letter-spacing:2px;text-transform:uppercase;
  padding:11px 18px;border:1px solid var(--red);background:transparent;color:var(--red2);
  cursor:pointer;transition:all .15s;display:inline-block;
}
.btn:hover:not(:disabled){background:rgba(185,28,28,.12);color:#fff;}
.btn.primary{background:var(--red);color:#fff;font-weight:700;}
.btn.primary:hover:not(:disabled){background:var(--red2);border-color:var(--red2);}
.btn.ghost{border-color:var(--border2);color:var(--text);}
.btn.ghost:hover:not(:disabled){border-color:var(--text);color:var(--bright);background:transparent;}
.btn.small{padding:7px 12px;font-size:10px;}
.btn:disabled{opacity:.35;cursor:not-allowed;}
.btn-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:6px;}

.msg{font-family:var(--fm);font-size:11px;letter-spacing:.5px;margin-top:14px;min-height:16px;}
.msg.ok{color:var(--ok);} .msg.err{color:var(--red2);}

.adv{margin-top:20px;border-top:1px dashed var(--border2);padding-top:16px;}
.adv-toggle{background:none;border:none;font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--text);cursor:pointer;text-transform:uppercase;}
.adv-toggle:hover{color:var(--red2);}
.adv-body{margin-top:14px;}

/* posts */
.counter{display:flex;align-items:center;gap:10px;font-family:var(--fm);font-size:11px;color:var(--text);letter-spacing:2px;}
.counter b{color:var(--white);font-weight:normal;min-width:28px;text-align:center;}
.post-card{background:var(--card);border:1px solid var(--border2);border-left:3px solid var(--red);padding:16px;margin-bottom:14px;}
.post-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;}
.post-num{font-family:var(--fm);font-size:11px;letter-spacing:3px;color:var(--red2);}
.link-btn{background:none;border:none;font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--dim);cursor:pointer;text-transform:uppercase;}
.link-btn:hover{color:var(--red2);}
.link-btn:disabled{opacity:.25;cursor:default;}
.check{display:flex;align-items:center;gap:10px;margin-top:12px;font-family:var(--fm);font-size:10px;letter-spacing:1.5px;color:var(--text);text-transform:uppercase;cursor:pointer;}
.check input{accent-color:var(--red2);width:15px;height:15px;}
.photo-row{display:flex;align-items:center;gap:12px;margin-top:12px;flex-wrap:wrap;}
.photo-name{font-family:var(--fm);font-size:10px;color:var(--text);word-break:break-all;}
.photo-name.set{color:var(--bright);}

.publish-bar{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;margin-top:18px;padding-top:18px;border-top:1px solid var(--border);}
.publish-bar .hint{font-family:var(--fm);font-size:10px;letter-spacing:2px;color:var(--dim);text-transform:uppercase;}

/* log */
.log-box{background:#050505;border:1px solid var(--border);height:360px;overflow-y:auto;padding:14px;font-family:var(--fm);font-size:11px;line-height:1.7;}
.log-line{white-space:pre-wrap;word-break:break-word;color:#aaa;}
.log-line.ok{color:var(--ok);}
.log-line.err{color:var(--red2);}
.log-line.warn{color:var(--warn);}
.log-line.dim{color:#555;}
.empty-log{color:#333;}

/* modal + toast */
.overlay{position:fixed;inset:0;background:rgba(0,0,0,.8);display:flex;align-items:center;justify-content:center;z-index:1000;padding:20px;}
.modal{background:var(--panel);border:1px solid var(--red);border-top:3px solid var(--red);max-width:440px;width:100%;padding:24px;}
.modal h3{font-family:var(--fh);font-size:28px;letter-spacing:2px;color:var(--white);margin-bottom:10px;}
.modal p{font-family:var(--fb);font-size:17px;color:var(--bright);line-height:1.4;white-space:pre-wrap;margin-bottom:20px;}
.modal .btn-row{justify-content:flex-end;}
.toast{position:fixed;bottom:24px;left:50%;transform:translate(-50%,20px);opacity:0;pointer-events:none;
  background:#000;border:1px solid var(--red);border-left:3px solid var(--red2);color:var(--bright);
  font-family:var(--fm);font-size:11px;letter-spacing:1.5px;padding:12px 18px;z-index:1001;transition:all .25s;max-width:90vw;}
.toast.show{opacity:1;transform:translate(-50%,0);}

.footer{margin-top:36px;padding-top:18px;border-top:1px solid var(--border);text-align:center;font-family:var(--fm);font-size:10px;letter-spacing:4px;color:var(--muted);}
.footer b{color:var(--red2);font-weight:normal;}
</style>
</head>
<body>
<div class="wrap">

  <div class="topbar">
    <div class="tbl">GRAPH<span>::</span>API &nbsp;/&nbsp; PAGE PUBLISHER</div>
    <div class="status"><span id="dot" class="dot"></span><span id="statusText">NOT CONNECTED</span></div>
  </div>

  <div class="masthead">
    <div class="logo">VOID<span class="slash">//</span>POST<span class="ver">v1.0</span></div>
    <div class="sub">Facebook Page publishing console</div>
  </div>

  <div class="tabs">
    <button class="tab on" data-tab="connect"><span class="n">01</span>Connect</button>
    <button class="tab" data-tab="compose"><span class="n">02</span>Compose</button>
    <button class="tab" data-tab="log"><span class="n">03</span>Log</button>
  </div>

  <!-- CONNECT -->
  <section class="panel" id="pane-connect">
    <div class="panel-head">
      <div><div class="sec-num">01 / CONNECTION</div><div class="sec-title">Connect your page</div></div>
    </div>
    <div class="row">
      <div class="field">
        <label class="lbl" for="pageId">Page ID</label>
        <input type="text" id="pageId" value="__PAGE_ID__" placeholder="e.g. 123456789012345">
      </div>
      <div class="field">
        <label class="lbl" for="token">Page access token</label>
        <input type="password" id="token" placeholder="Paste your token">
      </div>
    </div>
    <div class="btn-row">
      <button class="btn primary" id="testBtn">Test connection</button>
      <button class="btn ghost" id="saveBtn">Save credentials</button>
    </div>
    <div id="connMsg" class="msg"></div>

    <div class="adv">
      <button class="adv-toggle" id="advToggle">[ + ] Get a long-lived token</button>
      <div class="adv-body" id="advBody" hidden>
        <div class="row">
          <div class="field">
            <label class="lbl" for="appId">App ID</label>
            <input type="text" id="appId">
          </div>
          <div class="field">
            <label class="lbl" for="appSecret">App secret</label>
            <input type="password" id="appSecret">
          </div>
        </div>
        <div class="field">
          <label class="lbl" for="shortToken">Short-lived user token</label>
          <input type="password" id="shortToken">
        </div>
        <div class="btn-row">
          <button class="btn ghost" id="exchangeBtn">Exchange for long-lived token</button>
        </div>
      </div>
    </div>
  </section>

  <!-- COMPOSE -->
  <section class="panel" id="pane-compose" hidden>
    <div class="panel-head">
      <div><div class="sec-num">02 / CONTENT</div><div class="sec-title">Compose posts</div></div>
      <div class="counter">
        <button class="btn ghost small" id="minusBtn">−</button>
        <b id="postCount">1</b>
        <button class="btn ghost small" id="plusBtn">+</button>
        <span>/ <span id="maxCount"></span></span>
      </div>
    </div>

    <div id="posts"></div>

    <div class="publish-bar">
      <div class="hint" id="publishHint">Each post is published in order.</div>
      <button class="btn primary" id="publishBtn">Publish</button>
    </div>
  </section>

  <!-- LOG -->
  <section class="panel" id="pane-log" hidden>
    <div class="panel-head">
      <div><div class="sec-num">03 / OUTPUT</div><div class="sec-title">Activity log</div></div>
      <button class="btn ghost small" id="clearBtn">Clear</button>
    </div>
    <div class="log-box" id="log"></div>
  </section>

  <div class="footer">VOID<b>//</b>POST &nbsp;·&nbsp; GRAPH API v21.0</div>
</div>

<!-- confirm modal -->
<div class="overlay" id="modal" hidden>
  <div class="modal">
    <h3>Confirm</h3>
    <p id="modalText"></p>
    <div class="btn-row">
      <button class="btn ghost" id="mNo">Cancel</button>
      <button class="btn primary" id="mOk">Confirm</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const $ = id => document.getElementById(id);
const MAX_POSTS = __MAX_POSTS__;
let posts = [];          // [{el}]
let postSeq = 0;
let connected = false;

/* ---------- tabs ---------- */
function showTab(name){
  document.querySelectorAll('.tab').forEach(b => b.classList.toggle('on', b.dataset.tab === name));
  ['connect','compose','log'].forEach(n => $('pane-' + n).hidden = (n !== name));
}
document.querySelectorAll('.tab').forEach(b => b.onclick = () => showTab(b.dataset.tab));

/* ---------- status + log ---------- */
function setStatus(kind, text){
  $('dot').className = 'dot ' + kind;
  $('statusText').textContent = text.toUpperCase();
}
function logLine(msg, kind){
  const box = $('log');
  const empty = box.querySelector('.empty-log');
  if (empty) empty.remove();
  const d = document.createElement('div');
  d.className = 'log-line ' + (kind || '');
  d.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg;
  box.appendChild(d);
  box.scrollTop = box.scrollHeight;
}
$('clearBtn').onclick = () => { $('log').innerHTML = ''; logLine('Log cleared.', 'dim'); };

function toast(msg){
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.remove('show'), 3200);
}

function confirmBox(text){
  return new Promise(resolve => {
    $('modalText').textContent = text;
    $('modal').hidden = false;
    const done = v => {
      $('modal').hidden = true;
      $('mOk').onclick = null; $('mNo').onclick = null;
      resolve(v);
    };
    $('mOk').onclick = () => done(true);
    $('mNo').onclick = () => done(false);
  });
}

async function postJSON(url, body){
  const r = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  return r.json();
}

/* ---------- connection ---------- */
$('testBtn').onclick = async () => {
  const page_id = $('pageId').value.trim(), token = $('token').value.trim();
  const msg = $('connMsg');
  msg.className = 'msg'; msg.textContent = 'Checking...';
  setStatus('busy', 'Checking');
  try{
    const d = await postJSON('/api/test-connection', {page_id, token});
    if (d.ok){
      connected = true;
      msg.className = 'msg ok'; msg.textContent = 'Connected to ' + d.name + ' (ID ' + d.id + ')';
      setStatus('ok', 'Connected · ' + d.name);
      logLine('Connected to ' + d.name + '.', 'ok');
    } else throw new Error(d.error || 'Unknown error');
  } catch(e){
    connected = false;
    msg.className = 'msg err'; msg.textContent = 'Failed: ' + e.message;
    setStatus('err', 'Connection failed');
    logLine('Connection failed: ' + e.message, 'err');
  }
};

$('saveBtn').onclick = async () => {
  const d = await postJSON('/api/save-credentials', {
    page_id: $('pageId').value.trim(), token: $('token').value.trim()
  });
  if (d.ok){ toast('Credentials saved locally.'); logLine('Credentials saved to config file.', 'ok'); }
};

$('advToggle').onclick = () => {
  const open = $('advBody').hidden;
  $('advBody').hidden = !open;
  $('advToggle').textContent = (open ? '[ − ]' : '[ + ]') + ' Get a long-lived token';
};

$('exchangeBtn').onclick = async () => {
  const d = await postJSON('/api/exchange-token', {
    app_id: $('appId').value.trim(),
    app_secret: $('appSecret').value.trim(),
    short_token: $('shortToken').value.trim()
  });
  if (d.ok){
    $('token').value = d.token;
    toast('Long-lived token received and filled in.');
    logLine('Long-lived token obtained.', 'ok');
  } else {
    toast('Exchange failed: ' + d.error);
    logLine('Token exchange failed: ' + d.error, 'err');
  }
};

/* ---------- posts ---------- */
function renumber(){
  posts.forEach((p, i) => {
    p.el.querySelector('.post-num').textContent = 'POST ' + String(i + 1).padStart(2, '0');
    p.el.querySelector('.remove').disabled = posts.length === 1;
  });
  $('postCount').textContent = posts.length;
  $('minusBtn').disabled = posts.length === 1;
  $('plusBtn').disabled = posts.length >= MAX_POSTS;
}

function addPost(){
  if (posts.length >= MAX_POSTS) return;
  const id = ++postSeq;
  const el = document.createElement('div');
  el.className = 'post-card';
  el.innerHTML = `
    <div class="post-head">
      <span class="post-num"></span>
      <button class="link-btn remove">Remove</button>
    </div>
    <label class="lbl">Post text</label>
    <textarea class="post-text" placeholder="Write what you want to say..."></textarea>
    <label class="check"><input type="checkbox" class="has-photo"> Include a photo</label>
    <div class="photo-row" hidden>
      <label class="btn ghost small">Choose file
        <input type="file" accept="image/*" class="photo-file" hidden>
      </label>
      <span class="photo-name">No file selected</span>
    </div>`;
  const hasPhoto = el.querySelector('.has-photo');
  const row = el.querySelector('.photo-row');
  const file = el.querySelector('.photo-file');
  const name = el.querySelector('.photo-name');

  hasPhoto.onchange = () => { row.hidden = !hasPhoto.checked; };
  file.onchange = () => {
    const f = file.files[0];
    name.textContent = f ? f.name : 'No file selected';
    name.classList.toggle('set', !!f);
  };
  el.querySelector('.remove').onclick = () => {
    posts = posts.filter(p => p.id !== id);
    el.remove();
    renumber();
  };

  $('posts').appendChild(el);
  posts.push({id, el});
  renumber();
  return el;
}

$('plusBtn').onclick = () => addPost();
$('minusBtn').onclick = () => {
  if (posts.length === 1) return;
  const last = posts.pop();
  last.el.remove();
  renumber();
};

/* ---------- publish ---------- */
$('publishBtn').onclick = async () => {
  const page_id = $('pageId').value.trim(), token = $('token').value.trim();
  if (!page_id || !token){
    toast('Enter Page ID and token first.');
    showTab('connect'); return;
  }

  const meta = [], fd = new FormData();
  for (let i = 0; i < posts.length; i++){
    const el = posts[i].el;
    const msg = el.querySelector('.post-text').value.trim();
    const wantsPhoto = el.querySelector('.has-photo').checked;
    const file = el.querySelector('.photo-file').files[0];

    if (!msg && !(wantsPhoto && file)){
      toast('POST ' + (i + 1) + ' is empty.');
      showTab('compose'); return;
    }
    if (wantsPhoto && !file){
      toast('POST ' + (i + 1) + ': choose a photo or untick the box.');
      showTab('compose'); return;
    }
    const has_photo = wantsPhoto && !!file;
    meta.push({message: msg, has_photo});
    if (has_photo) fd.append('photo_' + i, file);
  }

  const ok = await confirmBox('Publish ' + posts.length + ' post(s) to your Facebook Page now?');
  if (!ok) return;

  fd.append('page_id', page_id);
  fd.append('token', token);
  fd.append('posts_meta', JSON.stringify(meta));

  $('publishBtn').disabled = true;
  setStatus('busy', 'Publishing');
  showTab('log');
  logLine('Publishing ' + posts.length + ' post(s)...', 'warn');

  try{
    const res = await fetch('/api/publish', {method:'POST', body: fd});
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || 'Unknown error');
    let failed = 0;
    data.results.forEach(r => {
      if (r.ok) logLine('POST ' + (r.index + 1) + ' published. ID: ' + r.id, 'ok');
      else { failed++; logLine('POST ' + (r.index + 1) + ' FAILED: ' + r.error, 'err'); }
    });
    if (failed) setStatus('err', failed + ' failed');
    else setStatus(connected ? 'ok' : 'idle', 'Published');
    logLine('Done.', 'dim');
  } catch(e){
    logLine('Publish error: ' + e.message, 'err');
    setStatus('err', 'Publish error');
  } finally {
    $('publishBtn').disabled = false;
  }
};

/* ---------- init ---------- */
$('maxCount').textContent = MAX_POSTS;
addPost();
logLine('System ready. Connect a page to begin.', 'dim');
</script>
</body>
</html>
"""


@app.route("/")
def index():
    cfg = load_config()
    page_id = htmllib.escape(cfg.get("page_id", ""), quote=True)
    html = PAGE.replace("__PAGE_ID__", page_id).replace("__MAX_POSTS__", str(MAX_POSTS))
    return Response(html, mimetype="text/html")


@app.route("/api/save-credentials", methods=["POST"])
def save_credentials():
    data = request.get_json(silent=True) or {}
    cfg = load_config()
    cfg["page_id"] = data.get("page_id", "").strip()
    cfg["token"] = data.get("token", "").strip()
    save_config(cfg)
    return jsonify({"ok": True})


@app.route("/api/test-connection", methods=["POST"])
def test_connection():
    data = request.get_json(silent=True) or {}
    page_id = data.get("page_id", "").strip()
    token = data.get("token", "").strip()
    if not page_id or not token:
        return jsonify({"ok": False, "error": "Missing Page ID or access token."}), 400
    try:
        resp = requests.get(f"{GRAPH_BASE}/{page_id}",
                            params={"fields": "name,id", "access_token": token},
                            timeout=30)
        resp.raise_for_status()
        info = resp.json()
        return jsonify({"ok": True, "name": info.get("name"), "id": info.get("id")})
    except requests.HTTPError as e:
        msg = graph_message(e.response, str(e)) if e.response is not None else str(e)
        return jsonify({"ok": False, "error": msg}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/exchange-token", methods=["POST"])
def exchange_token():
    data = request.get_json(silent=True) or {}
    try:
        resp = requests.get(f"{GRAPH_BASE}/oauth/access_token",
                            params={
                                "grant_type": "fb_exchange_token",
                                "client_id": data.get("app_id", "").strip(),
                                "client_secret": data.get("app_secret", "").strip(),
                                "fb_exchange_token": data.get("short_token", "").strip(),
                            },
                            timeout=30)
        resp.raise_for_status()
        return jsonify({"ok": True, "token": resp.json()["access_token"]})
    except requests.HTTPError as e:
        msg = graph_message(e.response, str(e)) if e.response is not None else str(e)
        return jsonify({"ok": False, "error": msg}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/publish", methods=["POST"])
def publish():
    page_id = request.form.get("page_id", "").strip()
    token = request.form.get("token", "").strip()
    try:
        posts_meta = json.loads(request.form.get("posts_meta", "[]"))
    except json.JSONDecodeError:
        return jsonify({"ok": False, "error": "Bad post data."}), 400

    if not page_id or not token:
        return jsonify({"ok": False, "error": "Missing Page ID or token."}), 400

    results = []
    for i, post in enumerate(posts_meta):
        message = post.get("message", "").strip()
        has_photo = post.get("has_photo", False)
        try:
            if has_photo:
                file_key = f"photo_{i}"
                if file_key not in request.files:
                    raise ValueError("Photo marked but no file received.")
                photo = request.files[file_key]
                resp = requests.post(
                    f"{GRAPH_BASE}/{page_id}/photos",
                    data={"caption": message, "access_token": token},
                    files={"source": (photo.filename, photo.stream, photo.mimetype)},
                    timeout=120,
                )
            else:
                resp = requests.post(
                    f"{GRAPH_BASE}/{page_id}/feed",
                    data={"message": message, "access_token": token},
                    timeout=60,
                )
            resp.raise_for_status()
            body = resp.json()
            results.append({"index": i, "ok": True,
                            "id": body.get("id") or body.get("post_id")})
        except requests.HTTPError as e:
            msg = graph_message(e.response, str(e)) if e.response is not None else str(e)
            results.append({"index": i, "ok": False, "error": msg})
        except Exception as e:
            results.append({"index": i, "ok": False, "error": str(e)})

    return jsonify({"ok": True, "results": results})


if __name__ == "__main__":
    print("VOID//POST running at http://127.0.0.1:5000")
    app.run(debug=False, port=5000)