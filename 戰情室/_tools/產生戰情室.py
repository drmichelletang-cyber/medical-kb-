# -*- coding: utf-8 -*-
"""
叮噹戰情室 產生器
讀 戰情室/ 底下的 .md（員工/專案/KPI/會議）→ 重生 戰情室.html（靜態快照）。
模式與醫學知識庫相同：.md = 真相來源，HTML = 拋棄式衍生視圖。永遠改 .md，不要手改 HTML。
用法：  python3 戰情室/_tools/產生戰情室.py
"""
import os, re, json, datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT  = os.path.dirname(_HERE)            # = 戰情室/ 資料夾
OUT   = os.path.join(ROOT, "戰情室.html")

def parse_fm(text):
    """解析 frontmatter（與知識庫同一套：扁平 key:value 與 [list]）。"""
    fm, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end].strip("\n"); body = text[end+4:].lstrip("\n")
            for line in block.split("\n"):
                if ":" not in line: continue
                k, v = line.split(":", 1); k = k.strip(); v = v.strip()
                if v.startswith("[") and v.endswith("]"):
                    inner = v[1:-1].strip(); items = []
                    if inner:
                        for it in inner.split(","):
                            it = it.strip().strip('"').strip("'").strip()
                            if it: items.append(it)
                    fm[k] = items
                else:
                    v = v.strip('"').strip("'")
                    if v.lower() == "true": fm[k] = True
                    elif v.lower() == "false": fm[k] = False
                    elif re.fullmatch(r"-?\d+", v): fm[k] = int(v)
                    else: fm[k] = v
    return fm, body

employees, projects, kpis, meetings = [], [], [], []
SKIP_DIRS = {"_tools", "_範本"}
for dp, dns, files in os.walk(ROOT):
    dns[:] = [d for d in dns if d not in SKIP_DIRS]
    for fn in files:
        if not fn.endswith(".md"): continue
        raw = open(os.path.join(dp, fn), encoding="utf-8").read()
        fm, body = parse_fm(raw)
        m = re.search(r"^#\s+(.+)$", body, re.M)
        title = m.group(1).strip() if m else fn[:-3]
        body_clean = re.sub(r"^#\s+.+$", "", body, count=1, flags=re.M).strip()
        rec = {"title": title, "fm": fm, "body": body_clean}
        t = fm.get("type")
        if   t == "employee": employees.append(rec)
        elif t == "project":  projects.append(rec)
        elif t == "kpi":      kpis.append(rec)
        elif t == "meeting":  meetings.append(rec)

# 整理成前端要的扁平結構
def emp_out(r):
    f = r["fm"]
    return {"id": f.get("emp_id", r["title"]), "name": r["title"], "avatar": f.get("avatar", "🙂"),
            "role": f.get("role", ""), "kind": f.get("kind", "agent"),
            "state": f.get("state", "idle"), "doing": f.get("doing", ""),
            "order": f.get("order", 99)}
def proj_out(r):
    f = r["fm"]
    return {"id": f.get("proj_id", ""), "name": r["title"], "owner": f.get("owner", ""),
            "collaborators": f.get("collaborators", []), "status": f.get("status", "planned"),
            "progress": int(f.get("progress", 0)), "priority": f.get("priority", "med"),
            "start": f.get("start", ""), "due": f.get("due", ""), "kpi": f.get("kpi", []),
            "body": r["body"]}
def kpi_out(r):
    f = r["fm"]
    return {"id": f.get("kpi_id", ""), "name": r["title"], "scope": f.get("scope", "annual"),
            "period": str(f.get("period", "")), "current": float(f.get("current", 0)),
            "target": float(f.get("target", 1)), "unit": f.get("unit", ""), "owner": f.get("owner", "")}
def meet_out(r):
    f = r["fm"]
    return {"id": f.get("meet_id", ""), "title": r["title"], "date": str(f.get("date", "")),
            "attendees": f.get("attendees", []), "projects": f.get("projects", []),
            "tag": f.get("tag", ""), "recording": f.get("recording", ""), "body": r["body"]}

employees = sorted([emp_out(r) for r in employees], key=lambda e: e["order"])
projects  = sorted([proj_out(r) for r in projects], key=lambda p: -p["progress"])
kpis      = [kpi_out(r) for r in kpis]
kpis.sort(key=lambda k: (0 if k["scope"] == "annual" else 1, k["name"]))
meetings  = sorted([meet_out(r) for r in meetings], key=lambda m: m["date"], reverse=True)

gen = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y/%m/%d %H:%M")
DATA = json.dumps({"employees": employees, "projects": projects, "kpis": kpis,
                   "meetings": meetings, "generated_at": gen}, ensure_ascii=False)

TMPL = r"""<!DOCTYPE html>
<html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>叮噹戰情室 · 一人公司儀錶板</title>
<style>
:root{--navy:#1E2761;--gold:#C5993A;--cream:#F5F0E8;--ink:#23262e;--line:#e3dccb;--paper:#fbf8f1;--muted:#8a8675;
--green:#3f8f5b;--blue:#3a4488;--red:#b3340f;
--serif:"Noto Serif TC","Songti TC",Georgia,serif;--sans:"PingFang TC","Noto Sans TC","Microsoft JhengHei",-apple-system,sans-serif;}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--cream);color:var(--ink);font-family:var(--sans);min-height:100vh}
header{background:var(--navy);color:#fff;padding:13px 24px;display:flex;align-items:center;gap:16px;border-bottom:3px solid var(--gold);position:sticky;top:0;z-index:20}
header h1{font-family:var(--serif);font-size:19px;margin:0;letter-spacing:.05em;font-weight:600}
header .sub{color:#c9cbe0;font-size:11.5px;letter-spacing:.05em}
header .snap{margin-left:auto;text-align:right}
header .snap b{font-family:var(--serif);font-size:14px;color:var(--gold);font-variant-numeric:tabular-nums}
header .snap span{display:block;font-size:10px;color:#b9bcd4;letter-spacing:.08em}
main{max-width:1280px;margin:0 auto;padding:20px 22px 60px}
.sect{margin:22px 2px 11px;font-family:var(--serif);font-size:15px;color:var(--navy);display:flex;align-items:center;gap:9px}
.sect:before{content:"";width:4px;height:16px;background:var(--gold);border-radius:2px}
.sect .more{margin-left:auto;font-family:var(--sans);font-size:11px;color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}
.kpi{background:#fff;border:1px solid var(--line);border-radius:13px;padding:15px 16px}
.kpi .scope{font-size:10.5px;letter-spacing:.1em;font-weight:600}
.kpi .scope.annual{color:var(--blue)}.kpi .scope.monthly{color:var(--gold)}
.kpi .name{font-size:13px;color:#444;margin:3px 0 9px;font-weight:600}
.kpi .big{font-family:var(--serif);font-size:27px;color:var(--navy);line-height:1}
.kpi .big small{font-size:13px;color:var(--muted);font-family:var(--sans)}
.kpi .bar{height:7px;border-radius:5px;background:#efe9da;margin:10px 0 6px;overflow:hidden}
.kpi .bar i{display:block;height:100%;border-radius:5px;background:linear-gradient(90deg,var(--gold),#dcb45e)}
.kpi.ok .bar i{background:linear-gradient(90deg,var(--green),#6fb98a)}
.kpi.behind .bar i{background:linear-gradient(90deg,var(--red),#d9694f)}
.kpi .foot{font-size:11px;color:var(--muted);display:flex;justify-content:space-between}
.kpi .tag{font-weight:600}.kpi.ok .tag{color:var(--green)}.kpi.risk .tag{color:#b07d1f}.kpi.behind .tag{color:var(--red)}
.cols{display:grid;grid-template-columns:1.45fr 1fr;gap:22px;align-items:start}
.pcard{background:#fff;border:1px solid var(--line);border-radius:12px;padding:13px 15px;margin-bottom:11px;cursor:pointer;transition:.15s}
.pcard:hover{border-color:var(--gold);box-shadow:0 3px 14px rgba(30,39,97,.06)}
.pcard .top{display:flex;align-items:center;gap:10px}
.pcard .pname{font-family:var(--serif);font-size:15px;color:var(--navy);font-weight:600}
.pcard .pid{font-size:10px;color:var(--muted);letter-spacing:.05em}
.st{margin-left:auto;font-size:10.5px;font-weight:700;padding:3px 10px;border-radius:20px;white-space:nowrap}
.st.in_progress{background:#e7ebf7;color:var(--blue)}.st.review{background:#f6ecd6;color:#956c19}
.st.blocked{background:#fbe3dc;color:var(--red)}.st.done{background:#e4f0e8;color:var(--green)}.st.planned{background:#eee9dd;color:var(--muted)}
.pcard .pbar{height:9px;border-radius:6px;background:#efe9da;margin:11px 0 7px;overflow:hidden}
.pcard .pbar i{display:block;height:100%;border-radius:6px;background:linear-gradient(90deg,var(--navy),#3a4488)}
.pcard .pmeta{display:flex;align-items:center;gap:10px;font-size:11.5px;color:var(--muted)}
.owner{display:inline-flex;align-items:center;gap:6px;color:#444;font-weight:600}
.av{width:22px;height:22px;border-radius:50%;background:var(--paper);border:1px solid var(--line);display:inline-flex;align-items:center;justify-content:center;font-size:13px}
.pct{margin-left:auto;font-family:var(--serif);color:var(--navy);font-weight:700;font-size:14px}
.due.soon{color:#b07d1f;font-weight:600}.due.over{color:var(--red);font-weight:600}
.agents{background:#fff;border:1px solid var(--line);border-radius:12px;padding:6px 4px}
.arow{display:flex;align-items:center;gap:11px;padding:11px 13px;border-bottom:1px solid #f1ecdd}
.arow:last-child{border-bottom:none}
.arow .av{width:34px;height:34px;font-size:18px;position:relative;flex:0 0 auto}
.sdot{position:absolute;right:-2px;bottom:-2px;width:11px;height:11px;border-radius:50%;border:2px solid #fff}
.sdot.working{background:var(--green)}.sdot.meeting{background:var(--blue)}.sdot.review{background:var(--gold)}
.sdot.blocked{background:var(--red)}.sdot.idle{background:#c4bca6}.sdot.offline{background:#c4bca6}
.arow .who{font-size:13.5px;color:var(--navy);font-weight:600}
.arow .role{font-size:10.5px;color:var(--muted);font-weight:400}
.arow .task{font-size:12px;color:#555;margin-top:2px;line-height:1.4}
.arow .rt{margin-left:auto;flex:0 0 auto}
.statelab{font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:20px}
.statelab.working{background:#e4f0e8;color:var(--green)}.statelab.meeting{background:#e7ebf7;color:var(--blue)}
.statelab.review{background:#f6ecd6;color:#956c19}.statelab.blocked{background:#fbe3dc;color:var(--red)}
.statelab.idle{background:#eee9dd;color:var(--muted)}.statelab.offline{background:#eee9dd;color:var(--muted)}
.msearch{display:flex;gap:9px;margin-bottom:11px}
.msearch input{flex:1;padding:10px 13px;border:1px solid var(--line);border-radius:9px;background:#fff;font-family:var(--sans);font-size:13.5px;color:var(--ink)}
.msearch input:focus{outline:none;border-color:var(--gold)}
.mlist{display:grid;grid-template-columns:repeat(3,1fr);gap:11px}
.mcard{background:#fff;border:1px solid var(--line);border-radius:11px;padding:12px 14px;cursor:pointer;transition:.15s}
.mcard:hover{border-color:var(--gold);background:var(--paper)}
.mcard .md{font-size:10.5px;color:var(--gold);font-weight:700;letter-spacing:.05em}
.mcard .mt{font-family:var(--serif);font-size:14px;color:var(--navy);font-weight:600;margin:4px 0 6px}
.mcard .matt{font-size:11px;color:var(--muted);line-height:1.5}
.mcard .mtag{display:inline-block;margin-top:7px;font-size:10px;background:var(--paper);border:1px solid var(--line);color:#7a7560;padding:1px 8px;border-radius:12px}
.mask{position:fixed;inset:0;background:rgba(30,39,97,.4);display:none;align-items:center;justify-content:center;z-index:40;padding:20px}
.mask.on{display:flex}
.modal{background:var(--paper);border-radius:15px;max-width:640px;width:100%;max-height:84vh;overflow:auto;border:1px solid var(--line);box-shadow:0 20px 60px rgba(30,39,97,.3)}
.modal .mh{background:var(--navy);color:#fff;padding:17px 22px;position:sticky;top:0}
.modal .mh .d{color:var(--gold);font-size:11.5px;font-weight:700;letter-spacing:.06em}
.modal .mh h3{margin:5px 0 0;font-family:var(--serif);font-size:18px;font-weight:600}
.modal .mb{padding:18px 24px 26px;font-size:13.5px;line-height:1.75;color:#3a3d44}
.modal .mb h2{color:var(--navy);font-family:var(--serif);font-size:15px;margin:16px 0 6px;border-bottom:1px solid var(--line);padding-bottom:4px}
.modal .mb h3{color:#3a3d6b;font-size:13.5px;margin:12px 0 4px}
.modal .mb ul{margin:6px 0;padding-left:1.3em}.modal .mb li{margin:4px 0}
.modal .mb p{margin:.5em 0}
.modal .mb .att{font-size:12px;color:var(--muted);margin:0 0 8px}
.modal .x{position:absolute;right:16px;top:15px;cursor:pointer;color:#c9cbe0;font-size:20px;line-height:1;background:none;border:none}
.modal .x:hover{color:#fff}
.modal a.rec{display:inline-block;margin-top:12px;font-size:12px;color:var(--blue);text-decoration:none;border-bottom:1px solid var(--gold)}
.foot-note{color:var(--muted);font-size:11.5px;margin-top:30px;border-top:1px solid var(--line);padding-top:12px;line-height:1.7}
.foot-note code{background:#eee4cf;padding:1px 6px;border-radius:5px;font-size:.9em;color:#6e5a2e}
@media(max-width:880px){.kpis{grid-template-columns:1fr 1fr}.cols{grid-template-columns:1fr}.mlist{grid-template-columns:1fr}}
</style></head><body>
<header>
  <div><h1>叮噹戰情室</h1><div class="sub">一人公司 · 全員戰情儀錶板</div></div>
  <div class="snap"><b id="gen">—</b><span>快照產生時間</span></div>
</header>
<main>
  <div class="sect">📊 KPI 戰況 <span class="more">年度目標 · 本月目標</span></div>
  <div class="kpis" id="kpis"></div>
  <div class="cols">
    <div>
      <div class="sect">📁 專案進度 <span class="more">點卡片看里程碑／卡點</span></div>
      <div id="projects"></div>
    </div>
    <div>
      <div class="sect">👥 員工狀態 <span class="more">最後回報</span></div>
      <div class="agents" id="agents"></div>
    </div>
  </div>
  <div class="sect">🗒️ 開會記錄 · 快速調閱 <span class="more">點卡片看全文</span></div>
  <div class="msearch"><input id="msearch" placeholder="搜尋會議標題、與會者、決議關鍵字…"></div>
  <div class="mlist" id="meetings"></div>
  <div class="foot-note">
    這是一份<b>靜態快照</b>：資料來源是 <code>戰情室/</code> 底下的 <code>.md</code> 檔。改完內容後重跑
    <code>python3 戰情室/_tools/產生戰情室.py</code> 即更新此頁。<b>永遠改 .md，不要手改這個 HTML。</b>
  </div>
</main>
<div class="mask" id="mask"><div class="modal" id="modal"></div></div>
<script>
const DATA = __DATA__;
const EMP = Object.fromEntries(DATA.employees.map(e=>[e.id,e]));
const STATE_LABEL = {working:"工作中",meeting:"開會中",review:"待審",blocked:"卡住",idle:"待命",offline:"離線"};
const STATUS_TEXT = {in_progress:"進行中",review:"待審核",blocked:"卡住",done:"完成",planned:"規劃中"};
document.getElementById("gen").textContent = DATA.generated_at;

// 迷你 Markdown 轉換器（自帶、離線可用；只需處理標題／清單／粗體／勾選）
function md(src){
  const esc=s=>s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  const inl=s=>esc(s).replace(/\*\*(.+?)\*\*/g,"<b>$1</b>").replace(/`(.+?)`/g,"<code>$1</code>")
                     .replace(/^\[ \]\s*/,"☐ ").replace(/^\[x\]\s*/i,"☑ ");
  let out="",inUl=false; const closeUl=()=>{if(inUl){out+="</ul>";inUl=false;}};
  (src||"").split("\n").forEach(ln=>{
    let m;
    if(m=ln.match(/^(#{1,6})\s+(.*)/)){closeUl();const h=Math.min(m[1].length,4);out+=`<h${h}>${inl(m[2])}</h${h}>`;}
    else if(m=ln.match(/^\s*[-*]\s+(.*)/)){if(!inUl){out+="<ul>";inUl=true;}out+=`<li>${inl(m[1])}</li>`;}
    else if(ln.trim()===""){closeUl();}
    else{closeUl();out+=`<p>${inl(ln)}</p>`;}
  });
  closeUl(); return out;
}

function kClass(p){return p>=0.9?"ok":p>=0.6?"risk":"behind"}
function kTag(p){return p>=1?"達標":p>=0.9?"接近達標":p>=0.6?"進行中":"落後"}
document.getElementById("kpis").innerHTML = DATA.kpis.map(k=>{
  const p=k.target?Math.min(1,k.current/k.target):0, c=kClass(p);
  const cur=Number.isInteger(k.current)?k.current:k.current.toFixed(1);
  return `<div class="kpi ${c}">
    <div class="scope ${k.scope}">${k.scope==="annual"?"年度 KPI · "+k.period:"本月 KPI · "+k.period}</div>
    <div class="name">${k.name}</div>
    <div class="big">${cur}<small> / ${k.target} ${k.unit}</small></div>
    <div class="bar"><i style="width:${(p*100).toFixed(0)}%"></i></div>
    <div class="foot"><span>${(p*100).toFixed(0)}%</span><span class="tag">${kTag(p)}</span></div></div>`;
}).join("") || `<div class="foot-note">尚未建立 KPI。到 戰情室/KPI/ 依範本新增。</div>`;

function dueClass(d){if(!d)return"";const days=(new Date(d)-new Date())/86400000;return days<0?"over":days<10?"soon":""}
document.getElementById("projects").innerHTML = DATA.projects.map((p,i)=>{
  const o=EMP[p.owner]||{name:p.owner||"未指派",avatar:"❓"};
  return `<div class="pcard" data-i="${i}">
    <div class="top"><div><span class="pname">${p.name}</span> <span class="pid">${p.id}</span></div>
      <span class="st ${p.status}">${STATUS_TEXT[p.status]||p.status}</span></div>
    <div class="pbar"><i style="width:${p.progress}%"></i></div>
    <div class="pmeta"><span class="owner"><span class="av">${o.avatar}</span>${o.name}</span>
      ${p.due?`<span class="due ${dueClass(p.due)}">截止 ${p.due}</span>`:""}
      <span class="pct">${p.progress}%</span></div></div>`;
}).join("") || `<div class="foot-note">尚未建立專案。到 戰情室/專案/ 依範本新增。</div>`;

document.getElementById("agents").innerHTML = DATA.employees.map(e=>`
  <div class="arow">
    <span class="av">${e.avatar}<span class="sdot ${e.state}"></span></span>
    <div style="flex:1;min-width:0">
      <div class="who">${e.name} <span class="role">· ${e.role}</span></div>
      <div class="task">${e.doing||"—"}</div></div>
    <div class="rt"><span class="statelab ${e.state}">${STATE_LABEL[e.state]||e.state}</span></div>
  </div>`).join("") || `<div class="foot-note">尚未建立員工。到 戰情室/員工/ 依範本新增。</div>`;

function renderMeetings(q=""){
  q=q.trim().toLowerCase();
  const list=DATA.meetings.filter(m=>!q||(m.title+m.tag+m.attendees.map(a=>(EMP[a]||{}).name||a).join("")+m.body).toLowerCase().includes(q));
  const box=document.getElementById("meetings");
  if(!list.length){box.innerHTML=`<div class="foot-note">找不到符合的會議記錄。</div>`;return;}
  box.innerHTML=list.map((m,i)=>{
    const att=m.attendees.map(a=>(EMP[a]||{}).name||a).join("、");
    return `<div class="mcard" data-id="${m.id}"><div class="md">${m.date}</div>
      <div class="mt">${m.title}</div><div class="matt">與會：${att||"—"}</div>
      ${m.tag?`<div class="mtag">#${m.tag}</div>`:""}</div>`;
  }).join("");
  box.querySelectorAll(".mcard").forEach(el=>el.onclick=()=>openMeeting(el.dataset.id));
}
function openMeeting(id){
  const m=DATA.meetings.find(x=>x.id===id);if(!m)return;
  const att=m.attendees.map(a=>(EMP[a]||{}).name||a).join("、");
  const rec=m.recording?`<a class="rec" href="${m.recording}" target="_blank">▶ 調閱錄影／逐字稿</a>`
    :`<a class="rec" href="#" onclick="return false">▶ 調閱錄影／逐字稿（之後接 Zoom）</a>`;
  document.getElementById("modal").innerHTML=`
    <div class="mh"><button class="x" onclick="closeModal()">×</button>
      <div class="d">${m.date}${m.tag?" · #"+m.tag:""}</div><h3>${m.title}</h3></div>
    <div class="mb"><div class="att">與會：${att||"—"}</div>${md(m.body||"（無內容）")}${rec}</div>`;
  document.getElementById("mask").classList.add("on");
}
function closeModal(){document.getElementById("mask").classList.remove("on")}
document.getElementById("mask").onclick=e=>{if(e.target.id==="mask")closeModal()};
document.getElementById("msearch").oninput=e=>renderMeetings(e.target.value);

document.querySelectorAll("#projects .pcard").forEach(el=>el.onclick=()=>{
  const p=DATA.projects[el.dataset.i];
  document.getElementById("modal").innerHTML=`
    <div class="mh"><button class="x" onclick="closeModal()">×</button>
      <div class="d">${p.id} · ${STATUS_TEXT[p.status]||p.status} · ${p.progress}%</div><h3>${p.name}</h3></div>
    <div class="mb"><div class="att">負責人：${(EMP[p.owner]||{}).name||p.owner||"未指派"}${p.due?" ｜ 截止 "+p.due:""}</div>
      ${md(p.body||"（無內容）")}</div>`;
  document.getElementById("mask").classList.add("on");
});
renderMeetings();
</script></body></html>"""

html = TMPL.replace("__DATA__", DATA)
open(OUT, "w", encoding="utf-8").write(html)
print("戰情室 HTML OK:", len(employees), "員工 /", len(projects), "專案 /",
      len(kpis), "KPI /", len(meetings), "會議")
