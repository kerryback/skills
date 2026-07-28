"""Browser capture form for a litdb note (`litdb note-form`, `/litdb:note`).

Zero-dependency (stdlib http.server + webbrowser), mirroring coauthor's roster
picker: it serves a one-screen form on 127.0.0.1, opens the browser, and BLOCKS
until the user submits (or the timeout). On submit it writes the note through the
normal db layer and returns the created note; `main()`/`run()` prints it as JSON so
the caller (the CLI, then Claude) can confirm what was saved.

Unlike the roster picker it needs no network — the paper picker queries the local
litdb DB in-process. A fresh db.connect() is opened per request so nothing is
shared across the server's handler threads.
"""

from __future__ import annotations

import json
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import db
from . import retrieval

NOTE_KINDS = db.NOTE_KINDS
RELATIONS = ("about", "supports", "contradicts", "extends", "uses-method", "uses-data")


def _page(prefill: list[dict], project: str | None, projects: list[str]) -> bytes:
    ctx = json.dumps({
        "prefill": prefill,
        "project": project or "",
        "projects": projects,
        "kinds": list(NOTE_KINDS),
        "relations": list(RELATIONS),
    })
    return _HTML.replace("__CTX__", ctx).encode("utf-8")


def _make_handler(prefill, project, projects, result: dict, done: threading.Event):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def _send(self, code: int, ctype: str, body: bytes):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            if u.path == "/":
                self._send(200, "text/html; charset=utf-8", _page(prefill, project, projects))
            elif u.path == "/api/search":
                qs = urllib.parse.parse_qs(u.query)
                q = (qs.get("q") or [""])[0].strip()
                results = []
                if q:
                    conn = db.connect()
                    for h in retrieval.keyword_search(conn, q, k=10, owner_type="paper"):
                        results.append({"id": h["id"], "title": h.get("title"),
                                        "authors": h.get("authors"), "year": h.get("year")})
                self._send(200, "application/json", json.dumps({"results": results}).encode())
            else:
                self._send(404, "text/plain", b"not found")

        def do_POST(self):
            u = urllib.parse.urlparse(self.path)
            if u.path != "/submit":
                self._send(404, "text/plain", b"not found")
                return
            length = int(self.headers.get("Content-Length", 0) or 0)
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                self._send(400, "application/json", json.dumps({"error": "bad json"}).encode())
                return
            body = (data.get("body") or "").strip()
            if not body:
                self._send(400, "application/json", json.dumps({"error": "empty body"}).encode())
                return
            conn = db.connect()
            nid = db.add_note(conn, body, title=(data.get("title") or None),
                              kind=(data.get("kind") or None),
                              confidential=bool(data.get("confidential")))
            for link in data.get("links", []):
                pid = link.get("paper_id")
                if not pid:
                    continue
                page = link.get("page")
                page = int(page) if str(page).strip().isdigit() else None
                db.link_note_paper(conn, nid, int(pid), (link.get("relation") or None),
                                   page=page, quote=(link.get("quote") or None))
            for name in data.get("projects", []):
                name = (name or "").strip()
                if name:
                    db.tag_project(conn, "note", nid, name, source="user")
            conn.commit()
            note = db.get_note(conn, nid) or {"note_id": nid}
            result.clear()
            result.update(note)
            result["submitted"] = True
            result["note_id"] = nid
            self._send(200, "application/json", json.dumps({"ok": True, "note_id": nid}).encode())
            done.set()

    return Handler


def run(*, prefill_papers=(), project: str | None = None, port: int = 0,
        timeout: int = 900, open_browser: bool = True) -> dict:
    """Serve the form, block until submit or timeout, return the created note
    dict (with `submitted: True`) or `{"submitted": False}`."""
    conn = db.connect()
    db.init_db(conn)
    prefill = []
    for pid in prefill_papers or []:
        r = conn.execute("SELECT id, title, authors, year FROM paper WHERE id=?", (pid,)).fetchone()
        if r:
            prefill.append({"id": r["id"], "title": r["title"],
                            "authors": r["authors"], "year": r["year"]})
    projects = [p.get("name") for p in db.list_projects(conn) if p.get("name")]

    result: dict = {}
    done = threading.Event()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), _make_handler(prefill, project, projects, result, done))
    real_port = httpd.server_address[1]
    url = f"http://127.0.0.1:{real_port}/"
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print(f"litdb note form at {url} — waiting up to {timeout}s for you to submit…",
          file=sys.stderr)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    done.wait(timeout)
    httpd.shutdown()
    return result if result else {"submitted": False}


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(prog="litdb note-form")
    ap.add_argument("--paper", type=int, action="append", default=[])
    ap.add_argument("--project")
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    out = run(prefill_papers=a.paper, project=a.project, port=a.port,
              timeout=a.timeout, open_browser=not a.no_browser)
    print(json.dumps(out, default=str))


_HTML = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>litdb — new note</title>
<style>
  :root { color-scheme: light dark; }
  body { font: 15px/1.5 system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
  h1 { font-size: 1.2rem; }
  label { display:block; font-weight:600; margin:.9rem 0 .25rem; }
  textarea, input[type=text], select { width:100%; box-sizing:border-box; padding:.5rem;
    font:inherit; border:1px solid #8886; border-radius:6px; background:transparent; color:inherit; }
  textarea { min-height:9rem; resize:vertical; }
  .row { border:1px solid #8884; border-radius:8px; padding:.6rem; margin:.5rem 0; }
  .row .line { display:flex; gap:.5rem; flex-wrap:wrap; align-items:center; }
  .row .line > * { flex:1 1 auto; }
  .results { border:1px solid #8886; border-radius:6px; margin-top:.25rem; max-height:11rem; overflow:auto; }
  .results div { padding:.35rem .5rem; cursor:pointer; }
  .results div:hover { background:#8882; }
  .chosen { font-weight:600; margin-top:.25rem; }
  .muted { color:#8889; font-weight:400; }
  button { font:inherit; padding:.45rem .8rem; border-radius:6px; border:1px solid #8886;
    background:#8881; color:inherit; cursor:pointer; }
  .primary { background:#3b82f6; color:#fff; border-color:#3b82f6; }
  .bar { display:flex; gap:.6rem; align-items:center; margin-top:1rem; }
  .small { width:6rem; flex:0 0 auto; }
  #msg { margin-top:1rem; }
</style></head>
<body>
<h1>New note <span class="muted">— litdb</span></h1>

<label>Note <span class="muted">(markdown)</span></label>
<textarea id="body" autofocus></textarea>

<label>Title <span class="muted">(optional)</span></label>
<input type="text" id="title">

<div class="line" style="display:flex; gap:1rem;">
  <div style="flex:1"><label>Kind</label><select id="kind"></select></div>
  <div style="flex:1"><label>Projects <span class="muted">(comma-separated)</span></label>
    <input type="text" id="projects" list="projlist"><datalist id="projlist"></datalist></div>
</div>

<label>Linked papers</label>
<div id="links"></div>
<button id="addlink" type="button">+ Add paper</button>

<label style="margin-top:1rem;"><input type="checkbox" id="confidential" style="width:auto"> Confidential (embed locally only)</label>

<div class="bar">
  <button class="primary" id="save" type="button">Save note</button>
  <span id="msg" class="muted"></span>
</div>

<script>
const CTX = __CTX__;
const $ = s => document.querySelector(s);

// kind select
const kindSel = $("#kind");
kindSel.innerHTML = '<option value="">(none)</option>' + CTX.kinds.map(k=>`<option>${k}</option>`).join("");
// project datalist + prefill
$("#projlist").innerHTML = CTX.projects.map(p=>`<option value="${p.replace(/"/g,'&quot;')}">`).join("");
if (CTX.project) $("#projects").value = CTX.project;

const linksEl = $("#links");
function addRow(pref){
  const row = document.createElement("div");
  row.className = "row";
  row.innerHTML = `
    <input type="text" class="q" placeholder="search a paper by title/author…">
    <div class="results" style="display:none"></div>
    <div class="chosen muted">no paper chosen</div>
    <div class="line" style="margin-top:.4rem">
      <select class="rel">${CTX.relations.map(r=>`<option>${r}</option>`).join("")}</select>
      <input type="text" class="page small" placeholder="page">
      <input type="text" class="quote" placeholder="verbatim quote (optional)">
      <button type="button" class="rm" style="flex:0 0 auto">remove</button>
    </div>`;
  linksEl.appendChild(row);
  const q = row.querySelector(".q"), res = row.querySelector(".results"), chosen = row.querySelector(".chosen");
  row.dataset.paperId = "";
  if (pref){ row.dataset.paperId = pref.id; chosen.textContent = `#${pref.id} ${pref.title||""}`; chosen.className="chosen"; }
  row.querySelector(".rm").onclick = ()=> row.remove();
  let t=null;
  q.oninput = ()=>{ clearTimeout(t); t=setTimeout(async()=>{
    const term=q.value.trim(); if(!term){res.style.display="none";return;}
    const r = await fetch("/api/search?q="+encodeURIComponent(term)); const j = await r.json();
    res.innerHTML = (j.results||[]).map(p=>`<div data-id="${p.id}">#${p.id} ${(p.title||"").replace(/</g,'&lt;')} <span class="muted">${(p.authors||"").split(";")[0]||""} ${p.year||""}</span></div>`).join("") || '<div class="muted">no matches</div>';
    res.style.display="block";
    res.querySelectorAll("div[data-id]").forEach(d=> d.onclick=()=>{
      row.dataset.paperId = d.dataset.id; chosen.textContent = d.textContent; chosen.className="chosen";
      res.style.display="none"; q.value="";
    });
  }, 200); };
  return row;
}
(CTX.prefill||[]).forEach(addRow);
if (!(CTX.prefill||[]).length) addRow(null);
$("#addlink").onclick = ()=> addRow(null);

$("#save").onclick = async ()=>{
  const body = $("#body").value.trim();
  if(!body){ $("#msg").textContent = "Note text is required."; return; }
  const links = [...document.querySelectorAll("#links .row")].filter(r=>r.dataset.paperId).map(r=>({
    paper_id: parseInt(r.dataset.paperId),
    relation: r.querySelector(".rel").value,
    page: r.querySelector(".page").value.trim(),
    quote: r.querySelector(".quote").value.trim(),
  }));
  const payload = {
    body, title: $("#title").value.trim(), kind: $("#kind").value,
    confidential: $("#confidential").checked,
    projects: $("#projects").value.split(",").map(s=>s.trim()).filter(Boolean),
    links,
  };
  $("#save").disabled = true; $("#msg").textContent = "Saving…";
  const r = await fetch("/submit", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload)});
  const j = await r.json();
  if(j.ok){ document.body.innerHTML = `<h1>Saved note #${j.note_id}</h1><p class="muted">You can close this tab and return to Claude.</p>`; setTimeout(()=>window.close(), 400); }
  else { $("#save").disabled=false; $("#msg").textContent = "Error: "+(j.error||"could not save"); }
};
</script>
</body></html>"""


if __name__ == "__main__":
    main()
