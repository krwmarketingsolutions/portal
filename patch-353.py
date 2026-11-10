#!/usr/bin/env python3
"""
patch-353.py (portal)  --  "Onboarding tracker" section on the Outreach tab

Sits directly under the Summary cards. One card per client being onboarded:
name, stage pill, one line summary, email underneath. Click a card and the
right-hand drawer opens with the full notes, a stage picker, and an "add a
note" box that appends a dated line. Everything reads and writes the backend
(server patch 353, GET/PUT /onboarding), so it is the same on the phone and
both Macs.

Backup: index.html.pre-353.bak    Safe to re-run: refuses twice.
Deploy: cd ~/krw/portal && git add index.html patch-353.py && git commit -m "patch 353: onboarding tracker on Outreach" && git push
"""
import os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
def find_root():
    for c in (HERE, os.path.dirname(HERE), os.getcwd(), os.path.dirname(os.getcwd()), os.path.expanduser("~/krw")):
        if os.path.isfile(os.path.join(c, "portal", "index.html")): return os.path.join(c, "portal")
        if os.path.isfile(os.path.join(c, "index.html")) and os.path.basename(c) == "portal": return c
ROOT = find_root() or sys.exit("STOPPED: run from ~/krw (needs portal/index.html)")
FILE = os.path.join(ROOT, "index.html")
src = open(FILE, encoding="utf-8").read()
if "patch 353" in src: sys.exit("patch 353 already applied - nothing to do")

edits = []
def rep(label, old, new): edits.append((label, old, new))

# 1. CSS, next to the other outreach styles
CSS_ANCHOR = "  #page-outreach button:focus-visible, #page-outreach input:focus-visible, #page-outreach select:focus-visible, #page-outreach textarea:focus-visible{outline:2px solid var(--lx-green);outline-offset:2px}"
CSS_NEW = CSS_ANCHOR + """
  /* patch 353: onboarding tracker */
  .ob-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px}
  .ob-card{background:var(--lx-white);border:1px solid var(--lx-line);border-left:4px solid var(--lx-green);padding:12px 14px 11px;cursor:pointer;transition:border-color .15s,transform .1s}
  .ob-card:hover{border-color:var(--lx-green);transform:translateY(-1px)}
  .ob-card .top{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
  .ob-card .nm{font-weight:600;font-size:16px;color:var(--lx-ink)}
  .ob-card .sum{font-size:14px;color:var(--lx-ink-2);margin-top:4px;line-height:1.4}
  .ob-card .em{font-size:13px;color:var(--lx-green);margin-top:6px;word-break:break-all}
  .ob-card .em.none{color:var(--lx-ink-3,#8a8578);font-style:italic}
  .ob-pill{display:inline-block;font-size:12px;padding:1px 8px;border-radius:2px;white-space:nowrap;border:1px solid transparent;background:var(--lx-brown-soft);color:var(--lx-brown);text-transform:capitalize}
  .ob-pill.live,.ob-pill.scaling{background:var(--lx-green-soft);color:var(--lx-green);border-color:#C4D3C8}
  .ob-pill.setup,.ob-pill.testing,.ob-pill.signed{background:#E4E9C7;color:#3E5A2A}
  .ob-notes{white-space:pre-wrap;font-size:14.5px;line-height:1.5;color:var(--lx-ink);background:var(--lx-white);border:1px solid var(--lx-line);padding:12px 14px;border-radius:3px}
  .ob-notes p{margin:0 0 8px}
  .ob-row{display:flex;gap:10px;align-items:center;margin:10px 0 14px;flex-wrap:wrap}
  .ob-row select,.ob-row input{font:inherit;font-size:14px;padding:6px 8px;border:1px solid var(--lx-line-2);border-radius:3px;background:var(--lx-white)}
  .ob-row input{flex:1;min-width:160px}
  .ob-add textarea{width:100%;box-sizing:border-box;font:inherit;font-size:14px;min-height:72px;padding:8px 10px;border:1px solid var(--lx-line-2);border-radius:3px;background:var(--lx-white)}"""
rep("css", CSS_ANCHOR, CSS_NEW)

# 2. Section markup, directly under Summary
HTML_ANCHOR = """        <!-- WORK QUEUE -->
        <div class="lx-section">
          <div class="lx-sechead"><h3>Needs you today</h3>"""
HTML_NEW = """        <!-- ONBOARDING TRACKER (patch 353) -->
        <div class="lx-section" id="ob-section">
          <div class="lx-sechead"><h3>Onboarding tracker</h3><span id="ob-sub" style="font-size:14px;color:var(--lx-ink-2)"></span></div>
          <p class="lx-lede">Buyers and partners being brought on right now. Click a name for the full notes, to move the stage, or to add a note.</p>
          <div class="ob-grid" id="ob-cards"><div style="color:var(--lx-ink-2);font-size:14px">Loading…</div></div>
        </div>

""" + HTML_ANCHOR
rep("html", HTML_ANCHOR, HTML_NEW)

# 3. JS: data, cards, drawer. Inserted right after the outreach store boots.
JS_ANCHOR = "orFetch();\nvar orView='board';"
JS_NEW = r"""orFetch();
// ── patch 353: onboarding tracker ─────────────────────────────────────────
var obData=[], obStages=[], obLoaded=false, obOpenId=null;
function obFetch(){
  fetch(OR_API+'/onboarding',{headers:{'x-api-key':OR_API_KEY_}})
  .then(function(r){return r.json();})
  .then(function(d){ if(!d.ok)throw new Error(d.error||'load failed'); obData=d.clients||[]; obStages=d.stages||[]; obLoaded=true; renderOb(); if(obOpenId!=null)obOpen(obOpenId,true); })
  .catch(function(e){ console.warn('[Onboarding] load failed:',e.message); var el=document.getElementById('ob-cards'); if(el)el.innerHTML='<div style="color:var(--lx-brown);font-size:14px">Could not load the onboarding list ('+lxEsc(e.message)+')</div>'; });
}
function obStageLabel(s){ return String(s||'').replace(/-/g,' '); }
function renderOb(){
  var el=document.getElementById('ob-cards'); if(!el)return;
  if(!obLoaded){ return; }
  if(!obData.length){ el.innerHTML='<div style="color:var(--lx-ink-2);font-size:14px">Nobody onboarding right now.</div>'; }
  else el.innerHTML=obData.map(function(c){
    return '<div class="ob-card" onclick="obOpen('+c.id+')">'+
      '<div class="top"><span class="nm">'+lxEsc(c.name)+(c.code?' <span style="font-weight:400;color:var(--lx-ink-2);font-size:13px">· '+lxEsc(c.code)+'</span>':'')+'</span><span class="ob-pill '+lxEsc(c.stage)+'">'+lxEsc(obStageLabel(c.stage))+'</span></div>'+
      '<div class="sum">'+lxEsc(c.summary||'')+'</div>'+
      (c.email?'<div class="em">'+lxEsc(c.email)+'</div>':'<div class="em none">no email on file</div>')+
    '</div>';
  }).join('');
  var sub=document.getElementById('ob-sub');
  if(sub){ var live=obData.filter(function(c){return c.stage==='live'||c.stage==='scaling';}).length; sub.textContent=obData.length+' onboarding · '+live+' live'; }
}
function obOpen(id,keep){
  var c=obData.find(function(x){return x.id===id;}); if(!c)return;
  obOpenId=id;
  document.getElementById('lx-d-name').textContent=c.name+(c.code?' · '+c.code:'');
  document.getElementById('lx-d-id').textContent='Onboarding';
  document.getElementById('lx-d-when').textContent='Updated '+new Date(c.updated_at).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
  var notes=String(c.notes||'').split('\n').filter(function(l){return l.trim();}).map(function(l){return '<p>'+lxEsc(l)+'</p>';}).join('')||'<p style="color:var(--lx-ink-2)">No notes yet.</p>';
  var html='<div class="lx-dsec"><h4>Status</h4>'+
    '<div class="ob-row"><select id="ob-stage" onchange="obSetStage('+c.id+',this.value)">'+obStages.map(function(s){return '<option value="'+s+'"'+(s===c.stage?' selected':'')+'>'+lxEsc(obStageLabel(s))+'</option>';}).join('')+'</select>'+
    '<input id="ob-email" placeholder="email" value="'+lxEsc(c.email||'')+'" onchange="obSetField('+c.id+',\'email\',this.value)">'+
    '</div>'+
    '<div style="font-size:14.5px;color:var(--lx-ink-2);margin-bottom:14px">'+lxEsc(c.summary||'')+'</div></div>'+
    '<div class="lx-dsec"><h4>Notes</h4><div class="ob-notes">'+notes+'</div></div>'+
    '<div class="lx-dsec ob-add"><h4>Add a note</h4><textarea id="ob-note" placeholder="What happened, what is next"></textarea>'+
    '<div class="ob-row" style="margin-top:8px"><button class="lx-btn" onclick="obAddNote('+c.id+')">Save note</button><button class="lx-btn quiet" onclick="obArchive('+c.id+')">Done onboarding (archive)</button></div></div>';
  document.getElementById('lx-dbody').innerHTML=html;
  if(!keep){ document.getElementById('lx-shade').classList.add('open'); var dr=document.getElementById('lx-drawer'); dr.classList.add('open'); dr.setAttribute('aria-hidden','false'); }
}
function obSetStage(id,stage){ obSetField(id,'stage',stage); }
function obSetField(id,k,v){
  var body={}; body[k]=v;
  fetch(OR_API+'/onboarding/'+id,{method:'PUT',headers:{'Content-Type':'application/json','x-api-key':OR_API_KEY_},body:JSON.stringify(body)})
  .then(function(r){return r.json();}).then(function(d){ if(!d.ok)throw new Error(d.error||'save failed'); showToast('Saved'); obFetch(); })
  .catch(function(e){ showToast('Save failed: '+e.message); });
}
function obAddNote(id){
  var t=document.getElementById('ob-note'); var note=t?t.value.trim():''; if(!note){showToast('Write the note first');return;}
  fetch(OR_API+'/onboarding/'+id+'/note',{method:'POST',headers:{'Content-Type':'application/json','x-api-key':OR_API_KEY_},body:JSON.stringify({note:note})})
  .then(function(r){return r.json();}).then(function(d){ if(!d.ok)throw new Error(d.error||'save failed'); showToast('Note added'); obFetch(); })
  .catch(function(e){ showToast('Save failed: '+e.message); });
}
function obArchive(id){
  if(!confirm('Mark this one as done onboarding? It comes off the list (not deleted).'))return;
  fetch(OR_API+'/onboarding/'+id,{method:'DELETE',headers:{'x-api-key':OR_API_KEY_}})
  .then(function(r){return r.json();}).then(function(d){ if(!d.ok)throw new Error(d.error||'failed'); showToast('Archived'); obOpenId=null; lxCloseProfile(); obFetch(); })
  .catch(function(e){ showToast('Failed: '+e.message); });
}
obFetch();
// ── end patch 353 ──────────────────────────────────────────────────────────
var orView='board';"""
rep("js", JS_ANCHOR, JS_NEW)

# 4. keep the drawer's close button from confusing the two drawers
rep("close hook", "function lxCloseProfile(){\n  LX.openId=null;", "function lxCloseProfile(){\n  LX.openId=null; if(typeof obOpenId!=='undefined')obOpenId=null;   // patch 353")

# 5. re-render the cards whenever the outreach page re-renders
rep("render hook",
    "function renderOutreach(){\n  if(typeof orData==='undefined')return;\n  renderOrStats(); renderOrToday(); renderLinkedIn();",
    "function renderOutreach(){\n  if(typeof orData==='undefined')return;\n  if(typeof renderOb==='function')renderOb();   // patch 353\n  renderOrStats(); renderOrToday(); renderLinkedIn();")

problems=[]
for label,old,new in edits:
    n=src.count(old)
    if n!=1: problems.append("%s: anchor found %d time(s), expected 1"%(label,n))
if problems:
    print("STOPPED - nothing changed. Anchors did not match:")
    for p in problems: print("  - "+p)
    sys.exit(1)
shutil.copyfile(FILE, FILE + ".pre-353.bak")
for label,old,new in edits: src=src.replace(old,new,1)
import re, time
stamp=time.strftime('%Y%m%d-%H%M%S')
src=re.sub(r"var KRW_BUILD = '[^']*';", "var KRW_BUILD = '"+stamp+"';", src, 1)
open(os.path.join(ROOT,'version.txt'),'w').write(stamp+'\n')
open(FILE,"w",encoding="utf-8").write(src)
print("Patched OK: %s"%FILE)
