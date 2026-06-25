# -*- coding: utf-8 -*-
import os, re, json
_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)   # vault 根目錄 = _tools 的上一層
OUT  = os.path.join(ROOT, "叮噹長壽知識庫_瀏覽器.html")
# GitHub Pages 根網址只認 index.html，故同時輸出一份同內容的 index.html
OUT_INDEX = os.path.join(ROOT, "index.html")
# 機器可讀的 KB 快照，供對話框後端（Supabase Edge Function）當 context 來源
OUT_JSON = os.path.join(ROOT, "notes.json")

def parse_fm(text):
    fm, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end].strip("\n"); body = text[end+4:].lstrip("\n")
            for line in block.split("\n"):
                if ":" not in line: continue
                k,v = line.split(":",1); k=k.strip(); v=v.strip()
                if v.startswith("[") and v.endswith("]"):
                    inner=v[1:-1].strip(); items=[]
                    if inner:
                        for it in inner.split(","):
                            it=it.strip().strip('"').strip("'").strip()
                            if it: items.append(it)
                    fm[k]=items
                else:
                    v=v.strip('"').strip("'")
                    if v.lower()=="true": fm[k]=True
                    elif v.lower()=="false": fm[k]=False
                    elif v.isdigit(): fm[k]=int(v)
                    else: fm[k]=v
    return fm, body

notes=[]
for dp,_,files in os.walk(ROOT):
    for fn in files:
        if not fn.endswith(".md"): continue
        rel=os.path.relpath(os.path.join(dp,fn),ROOT); folder=os.path.dirname(rel) or "."
        base=fn[:-3]; raw=open(os.path.join(dp,fn),encoding="utf-8").read()
        fm,body=parse_fm(raw)
        m=re.search(r"^#\s+(.+)$",body,re.M); title=m.group(1).strip() if m else base
        notes.append({"id":base,"folder":folder,"file":base,"title":title,"fm":fm,"body":body})

order=[".","01 9S框架","02 老年醫學證據庫","03 臨床主題","_範本"]
notes.sort(key=lambda n:((order.index(n["folder"]) if n["folder"] in order else 99), n["file"]))
data=json.dumps(notes,ensure_ascii=False)

TMPL=r"""<!DOCTYPE html>
<html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>叮噹長壽知識庫</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.0/marked.min.js"></script>
<style>
:root{--navy:#1E2761;--gold:#C5993A;--cream:#F5F0E8;--ink:#23262e;--line:#e3dccb;--paper:#fbf8f1;--muted:#8a8675;
--serif:"Noto Serif TC","Songti TC",Georgia,serif;--sans:"PingFang TC","Noto Sans TC","Microsoft JhengHei",-apple-system,sans-serif;}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:var(--cream);color:var(--ink);font-family:var(--sans);display:flex;flex-direction:column;height:100vh;overflow:hidden}
header{background:var(--navy);color:#fff;padding:14px 22px;display:flex;align-items:baseline;gap:18px;border-bottom:3px solid var(--gold);flex:0 0 auto}
header h1{font-family:var(--serif);font-size:20px;margin:0;letter-spacing:.04em;font-weight:600}
header .sub{color:#c9cbe0;font-size:12px;letter-spacing:.05em}
header .stats{margin-left:auto;display:flex;gap:16px;font-size:12px}
header .stats b{font-family:var(--serif);font-size:17px;color:var(--gold);display:block;line-height:1}
header .stats span{color:#b9bcd4;font-size:10.5px;letter-spacing:.08em}
.stat{text-align:right}
.wrap{flex:1;display:flex;min-height:0}
nav{width:300px;flex:0 0 auto;background:var(--paper);border-right:1px solid var(--line);overflow:auto;padding:14px 0}
.hubrow{margin:0 16px 10px;padding:9px 12px;border-radius:8px;background:var(--navy);color:#fff;font-size:13.5px;cursor:pointer;display:flex;align-items:center;gap:8px;font-weight:600}
.hubrow:hover{background:#2a3478}.hubrow.active{outline:2px solid var(--gold)}
nav .search{padding:0 16px 10px}
nav input{width:100%;padding:8px 11px;border:1px solid var(--line);background:#fff;border-radius:7px;font-family:var(--sans);font-size:13px;color:var(--ink)}
nav input:focus{outline:none;border-color:var(--gold)}
.group-h{font-size:11px;letter-spacing:.12em;color:var(--muted);padding:9px 16px 5px;font-weight:600}
.item{display:flex;align-items:center;gap:8px;padding:7px 16px 7px 22px;font-size:13.5px;cursor:pointer;border-left:3px solid transparent;color:#3a3d44}
.item:hover{background:#f1ebdd}
.item.active{background:#eee4cf;border-left-color:var(--gold);color:var(--navy);font-weight:600}
.dot{width:7px;height:7px;border-radius:50%;flex:0 0 auto}
.dot.v{background:#3f8f5b}.dot.u{background:var(--gold)}.dot.n{background:#c4bca6}
main{flex:1;overflow:auto;padding:38px 50px 80px}
.reading{max-width:760px;margin:0 auto;animation:fade .4s ease both}
@keyframes fade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.crumb{font-size:11.5px;color:var(--muted);letter-spacing:.08em;margin-bottom:4px}
.props{background:var(--paper);border:1px solid var(--line);border-radius:11px;padding:16px 18px;margin:14px 0 26px;font-size:13px}
.props .row{display:flex;gap:10px;padding:3px 0;align-items:baseline}
.props .k{flex:0 0 86px;color:var(--muted);font-size:11.5px;letter-spacing:.06em}
.badge{display:inline-flex;align-items:center;gap:6px;padding:3px 11px;border-radius:30px;font-size:12px;font-weight:600}
.badge.v{background:#e4f0e8;color:#2c6b43;border:1px solid #bcdcc7}
.badge.u{background:#f6ecd6;color:#956c19;border:1px solid #e6d3a4}
.chip{display:inline-block;padding:2px 10px;margin:2px 5px 2px 0;border-radius:20px;background:#fff;border:1px solid var(--line);font-size:11.5px;color:#5a5647}
.chip.link{cursor:pointer;border-color:#cdd0e6;color:var(--navy);background:#f3f4fb}
.chip.link:hover{background:var(--navy);color:#fff}
.tag{background:#f6ecd6;color:#956c19;padding:1px 8px;border-radius:5px;font-size:.9em;font-weight:600}
.note{font-family:var(--serif);line-height:1.85;font-size:16px;color:#2b2e36}
.note h1{font-size:27px;color:var(--navy);margin:.2em 0 .5em;line-height:1.3;border-bottom:2px solid var(--gold);padding-bottom:.3em;display:inline-block}
.note h2{font-size:20px;color:var(--navy);margin:1.5em 0 .5em;font-weight:600}
.note h3{font-size:16.5px;color:#3a3d6b;margin:1.2em 0 .4em}
.note p{margin:.7em 0}.note ul,.note ol{margin:.6em 0;padding-left:1.4em}.note li{margin:.32em 0}
.note strong{color:var(--navy)}
.note blockquote{border-left:4px solid var(--gold);background:#faf3e2;margin:1em 0;padding:.7em 1.1em;border-radius:0 8px 8px 0;color:#6e5a2e;font-size:15px}
.note table{border-collapse:collapse;width:100%;margin:1em 0;font-family:var(--sans);font-size:13px}
.note th{background:var(--navy);color:#fff;padding:8px 11px;text-align:left}
.note td{padding:8px 11px;border-bottom:1px solid var(--line)}
.note tr:nth-child(even) td{background:var(--paper)}
.note code{background:#eee4cf;padding:1px 6px;border-radius:5px;font-size:.88em;font-family:ui-monospace,Menlo,monospace;color:#6e5a2e}
.note pre{background:#1f2233;color:#e6e6f0;padding:14px 16px;border-radius:9px;overflow:auto;font-size:13px}
.note pre code{background:none;color:inherit;padding:0}
.note a.wl{color:var(--navy);text-decoration:none;border-bottom:1.5px solid var(--gold);cursor:pointer}
.note a.wl:hover{background:#faf3e2}
.note a.wl.broken{color:#b3340f;border-bottom:1.5px dashed #d98a72;cursor:default}
.note hr{border:none;border-top:1px solid var(--line);margin:1.6em 0}
.hint{color:var(--muted);font-size:12px;margin-top:36px;font-family:var(--sans);border-top:1px solid var(--line);padding-top:14px}
.hub{animation:fade .4s both}
.hub .lede{font-family:var(--serif);font-size:15px;color:#5a5647;margin:2px 0 24px;max-width:640px;line-height:1.75}
.pipe{display:flex;align-items:stretch;margin:0 0 6px;flex-wrap:wrap}
.pstep{flex:1;min-width:128px;background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:12px 13px}
.pstep .n{font-family:var(--serif);color:var(--gold);font-size:12px;font-weight:700}
.pstep .t{font-size:13px;color:var(--navy);font-weight:600;margin:3px 0}
.pstep .d{font-size:11px;color:var(--muted);line-height:1.5}
.parrow{display:flex;align-items:center;color:var(--gold);font-size:17px;padding:0 5px}
.pipenote{font-size:11.5px;color:var(--muted);margin:0 0 26px}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:0 0 8px}
.tile{background:#fff;border:1px solid var(--line);border-radius:11px;padding:15px 16px}
.tile b{font-family:var(--serif);font-size:29px;color:var(--navy);display:block;line-height:1}
.tile.v b{color:#2c6b43}.tile.u b{color:#956c19}
.tile span{font-size:11.5px;color:var(--muted)}
.sect{margin:28px 0 10px;font-family:var(--serif);font-size:17px;color:var(--navy);border-bottom:1px solid var(--line);padding-bottom:6px}
.qrow{display:flex;align-items:center;gap:10px;padding:8px 12px;border:1px solid var(--line);border-radius:9px;background:var(--paper);margin:6px 0;cursor:pointer;font-size:13.5px;color:#3a3d44}
.qrow:hover{border-color:var(--gold);background:#faf3e2}
.qrow .qb{margin-left:auto;font-size:11px;color:#956c19;background:#f6ecd6;border:1px solid #e6d3a4;padding:2px 9px;border-radius:20px;font-weight:600}
.qrow .qb.v{color:#2c6b43;background:#e4f0e8;border-color:#bcdcc7}
.pgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}
.pcard{border:1px solid var(--line);border-radius:9px;padding:11px 12px;background:#fff;cursor:pointer}
.pcard:hover{border-color:var(--gold);background:#faf3e2}
.pcard .pc{font-family:var(--serif);color:var(--navy);font-weight:600;font-size:14px}
.pcard .pp{font-size:10.5px;color:var(--muted);margin-top:3px}
.menubtn{display:none}
@media(max-width:760px){nav{position:fixed;z-index:5;height:calc(100% - 56px);transform:translateX(-100%);transition:.25s}nav.open{transform:none}
main{padding:24px 20px 70px}header .stats{display:none}.menubtn{display:inline-block;background:none;border:1px solid #4a4f86;color:#fff;border-radius:7px;padding:4px 10px;cursor:pointer}
.tiles{grid-template-columns:repeat(2,1fr)}.pgrid{grid-template-columns:1fr 1fr}.pipe{flex-direction:column}.parrow{transform:rotate(90deg);padding:3px 0}}
</style></head><body>
<header><button class="menubtn" onclick="document.querySelector('nav').classList.toggle('open')">☰</button>
<div><h1>叮噹長壽知識庫</h1><div class="sub">9S 為中心 · 老年醫學為地基 · 知識層</div></div>
<div class="stats" id="stats"></div></header>
<div class="wrap"><nav id="nav"></nav><main><div class="reading" id="reading"></div></main></div>
<script>
const NOTES=__DATA__;
const byId={},aliasIdx={};
NOTES.forEach(n=>{byId[n.id]=n;[n.file,n.title].concat(n.fm.aliases||[]).forEach(k=>{if(k)aliasIdx[String(k).trim().toLowerCase()]=n.id;});});
function resolve(t){return aliasIdx[String(t).trim().toLowerCase()]||null;}
const GROUPS=[".","01 9S框架","02 老年醫學證據庫","03 臨床主題","_範本"];
const GLABEL={".":"入口 · 索引","01 9S框架":"9S 框架","02 老年醫學證據庫":"老年醫學證據庫","03 臨床主題":"臨床主題","_範本":"範本"};
function vclass(n){if(n.fm.type==="evidence"||n.fm.type==="topic")return n.fm.verified===true?"v":"u";return "n";}
const okEv=NOTES.filter(n=>n.fm.type==="evidence"&&n.fm.verified===true).length;
const pending=NOTES.filter(n=>n.fm.verified===false&&n.folder!=="_範本").length;
document.getElementById("stats").innerHTML=
 `<div class="stat"><b>${NOTES.length}</b><span>筆記</span></div>`+
 `<div class="stat"><b>${okEv}</b><span>已查核</span></div>`+
 `<div class="stat"><b>${pending}</b><span>待查核</span></div>`;
function buildNav(filter=""){
  const nav=document.getElementById("nav");
  let h=`<div class="hubrow" id="hubbtn">⌂ Hub 首頁</div><div class="search"><input id="q" placeholder="搜尋筆記…" value="${filter}"></div>`;
  GROUPS.forEach(g=>{
    let items=NOTES.filter(n=>n.folder===g);
    if(filter) items=items.filter(n=>n.title.toLowerCase().includes(filter.toLowerCase()));
    if(!items.length) return;
    h+=`<div class="group-h">${GLABEL[g]||g}</div>`;
    items.forEach(n=>{h+=`<div class="item" data-id="${n.id}"><span class="dot ${vclass(n)}"></span>${n.title}</div>`;});
  });
  nav.innerHTML=h;
  nav.querySelectorAll(".item").forEach(el=>el.onclick=()=>{open(el.dataset.id);if(window.innerWidth<=760)nav.classList.remove("open");});
  const hb=document.getElementById("hubbtn"); if(hb) hb.onclick=()=>{renderHub();if(window.innerWidth<=760)nav.classList.remove("open");};
  const q=document.getElementById("q"); q.oninput=e=>buildNav(e.target.value); q.focus(); q.setSelectionRange(filter.length,filter.length);
}
function preprocess(md){return md.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,(m,t,a)=>{const disp=(a||t).trim();const id=resolve(t.trim());return id?`<a class="wl" data-nav="${id}">${disp}</a>`:`<a class="wl broken" title="尚未建立">${disp}</a>`;});}
function supportsHtml(n){const s=n.fm.supports||[];return s.map(item=>{const m=String(item).match(/\[\[([^\]|]+)\]\]/);if(m){const id=resolve(m[1].trim());return id?`<span class="chip link" data-nav="${id}">${m[1].trim()}</span>`:`<span class="chip">${m[1].trim()}</span>`;}return `<span class="chip">${item}</span>`;}).join("");}
function pstep(n,t,d){return `<div class="pstep"><div class="n">${n}</div><div class="t">${t}</div><div class="d">${d}</div></div>`;}
function renderHub(){
  document.querySelectorAll(".item").forEach(e=>e.classList.remove("active"));
  const hb=document.getElementById("hubbtn"); if(hb) hb.classList.add("active");
  const pillars=NOTES.filter(n=>n.fm.type==="pillar"&&n.fm.pillar_code&&n.fm.pillar_code!=="9S"&&n.fm.pillar_code!=="核心");
  const queue=NOTES.filter(n=>n.fm.verified===false&&n.folder!=="_範本");
  const ev=NOTES.filter(n=>n.fm.type==="evidence"&&n.fm.verified===true);
  const pipe=`<div class="pipe">`+pstep("1","看到醫學資訊","期刊・新聞・同行觀察")+`<div class="parrow">→</div>`+
    pstep("2","Claude 查核・分析","驗證出處、核對數字、標證據強度")+`<div class="parrow">→</div>`+
    pstep("3","醫學知識庫","唯一真相來源，結構化歸檔")+`<div class="parrow">→</div>`+
    pstep("4","HTML Hub 呈現","從 vault 重生此頁，易讀")+
    `</div><div class="pipenote">＊ 步驟 3→4 的更新由 Mac 上的監看器重跑產生器完成；此頁為靜態快照。</div>`;
  const tiles=`<div class="tiles"><div class="tile"><b>${NOTES.length}</b><span>總筆記</span></div>`+
    `<div class="tile v"><b>${ev.length}</b><span>已查核文獻</span></div>`+
    `<div class="tile u"><b>${queue.length}</b><span>待查核</span></div>`+
    `<div class="tile"><b>${pillars.length}</b><span>9S 支柱</span></div></div>`;
  const qlist=queue.length?queue.map(n=>`<div class="qrow" data-nav="${n.id}">${n.title}<span class="qb">待查核</span></div>`).join(""):`<div class="pipenote">目前沒有待查核項目。</div>`;
  const evlist=ev.map(n=>`<div class="qrow" data-nav="${n.id}">${n.title}<span class="qb v">✓ ${n.fm.evidence_grade||""}</span></div>`).join("");
  const pgrid=`<div class="pgrid">`+pillars.map(n=>`<div class="pcard" data-nav="${n.id}"><div class="pc">${n.fm.pillar_code} ${n.fm.pillar_en||""}</div><div class="pp">${n.fm.philosophy||""}</div></div>`).join("")+`</div>`;
  document.getElementById("reading").innerHTML=`<div class="hub"><div class="crumb">HUB · 知識層控制台</div>`+
    `<div class="note"><h1>叮噹長壽知識庫</h1></div>`+
    `<div class="lede">看到醫學資訊 → 我查核分析 → 存進醫學知識庫（真相來源）→ 重生這個 HTML 門面。以下是目前的庫存與待辦。</div>`+
    pipe+tiles+`<div class="sect">⏳ 待查核佇列</div>${qlist}`+`<div class="sect">✅ 已查核文獻</div>${evlist}`+`<div class="sect">🧭 9S 支柱</div>${pgrid}</div>`;
  document.querySelectorAll("[data-nav]").forEach(el=>el.onclick=()=>open(el.dataset.nav));
  document.querySelector("main").scrollTop=0;
}
function open(id){
  const n=byId[id]; if(!n) return;
  document.querySelectorAll(".item").forEach(e=>e.classList.toggle("active",e.dataset.id===id));
  const hb=document.getElementById("hubbtn"); if(hb) hb.classList.remove("active");
  const f=n.fm; let rows="";
  const add=(k,v)=>{if(v!==undefined&&v!==""&&!(Array.isArray(v)&&!v.length))rows+=`<div class="row"><div class="k">${k}</div><div class="val">${v}</div></div>`;};
  if(f.type)add("類型",f.type); if(f.citation)add("引用",f.citation); if(f.study_type)add("研究設計",f.study_type);
  if(f.evidence_grade)add("證據強度",f.evidence_grade); if(f.philosophy)add("東方哲學",f.philosophy);
  if(f.type==="evidence"||f.type==="topic"){const ok=f.verified===true;add("查核狀態",`<span class="badge ${ok?'v':'u'}">${ok?'✓ 已查核':'⏳ 待查核'}</span>`+(f.verified_date?` <span style="color:var(--muted);font-size:11px">${f.verified_date}</span>`:""));}
  const sup=supportsHtml(n); if(sup)add("支撐／連結",sup);
  const tg=(f.tags||[]).map(x=>`<span class="chip">#${x}</span>`).join(""); if(tg)add("標籤",tg);
  let body=n.body.replace(/^#\s+.+$/m,"").trim(); body=preprocess(body);
  let rendered=marked.parse(body,{breaks:false,gfm:true});
  rendered=rendered.replace(/(^|[\s(（>])#([\u4e00-\u9fa5A-Za-z0-9_\/]+)/g,'$1<span class="tag">#$2</span>');
  document.getElementById("reading").innerHTML=`<div class="crumb">${GLABEL[n.folder]||n.folder}</div>`+
    `<div class="note"><h1>${n.title}</h1></div>`+(rows?`<div class="props">${rows}</div>`:"")+
    `<div class="note">${rendered}</div>`+
    `<div class="hint">唯讀預覽。點 [[連結]] 可在筆記間跳轉；改完 .md 後重跑 _tools/產生HTML.py 即更新此頁。</div>`;
  document.querySelectorAll("[data-nav]").forEach(el=>el.onclick=()=>open(el.dataset.nav));
  document.querySelector("main").scrollTop=0;
}
buildNav(); renderHub();
</script></body></html>"""

html = TMPL.replace("__DATA__",data)
open(OUT,"w",encoding="utf-8").write(html)
open(OUT_INDEX,"w",encoding="utf-8").write(html)
open(OUT_JSON,"w",encoding="utf-8").write(data)
print("HTML OK,", len(notes), "notes (+ index.html + notes.json)")
