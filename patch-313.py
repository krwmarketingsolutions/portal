#!/usr/bin/env python3
"""
patch-313.py  --  Outreach command center: smart Email button, LinkedIn
                  section with pipeline, follow-up autopilot, copy-message,
                  editable templates (Kyler, Oct 7)

WHAT IT ADDS (portal/index.html)
  1. SMART EMAIL BUTTON (Needs you today): clicking Email opens Outlook/mail
     with a preloaded message chosen by how many emails this contact already
     got: 0 sent = intro, 1 = follow up, 2+ = bump. Name and firm merge in,
     the send is logged automatically (count, date, cold -> contacted).
  2. EDITABLE TEMPLATES: the Email view gains a "Email templates" editor
     (3 emails with subject+body, plus the LinkedIn follow up text). Saved to
     the server so they work from every device. Merge fields {{first_name}},
     {{name}}, {{firm}}.
  3. LINKEDIN SECTION: new panel under Needs you today listing every contact
     tagged LinkedIn with a pipeline strip (Messaged / Responded / In talks /
     Meetings / response rate) and one-tap buttons per row: Responded,
     In talks, Meeting set, Copy message (the agent's drafted text), Mark sent.
  4. NEW STAGE "Meeting set" across the board, filters and pills.
  5. FOLLOW-UP AUTOPILOT: a LinkedIn contact messaged 4+ days ago with no
     reply surfaces in Needs you today with a one-tap "Copy follow up".

  Pairs with patch 314 (backend: template store, draft text capture, reply
  sync). Build stamp bumped so open tabs self-update.

Usage (from ~/krw/portal):
    python3 patch-313.py
    git add -A && git commit -m "patch 313: outreach command center" && git push

Backup: index.html.pre-313.bak. Safe to re-run.
"""
import os, re, shutil, sys, datetime

TARGET = "index.html"
if not os.path.exists(TARGET):
    sys.exit("index.html not found - run this from ~/krw/portal")
src = open(TARGET, encoding="utf-8").read()
if "patch 313" in src:
    sys.exit("patch 313 already applied - nothing to do")

def must(label, old, new):
    global src
    n = src.count(old)
    if n != 1:
        sys.exit("%s: expected 1 match, found %d - aborting, index.html untouched" % (label, n))
    src = src.replace(old, new, 1)

# ── 1. Meeting set stage ──────────────────────────────────────────────────────
must("STAGES",
"var STAGES=['cold','contacted','responded','intalks','ready'];",
"var STAGES=['cold','contacted','responded','intalks','meeting','ready'];   // patch 313: Meeting set")
must("STAGE_LABELS",
"var STAGE_LABELS={cold:'Cold',contacted:'Contacted',responded:'Responded',intalks:'In Talks',ready:'Ready to Deal'};",
"var STAGE_LABELS={cold:'Cold',contacted:'Contacted',responded:'Responded',intalks:'In Talks',meeting:'Meeting set',ready:'Ready to Deal'};")
must("board col css",
'  .oz-col[data-stage="ready"]{border-top-color:var(--lx-green)}',
'  .oz-col[data-stage="meeting"]{border-top-color:var(--lx-green-2)} /* patch 313 */\n  .oz-col[data-stage="ready"]{border-top-color:var(--lx-green)}')
must("pill css",
"  .oz-pill.ready{background:var(--lx-green);color:var(--lx-paper);border-color:var(--lx-green)}",
"  .oz-pill.ready{background:var(--lx-green);color:var(--lx-paper);border-color:var(--lx-green)}\n  .oz-pill.meeting{background:var(--lx-green-2);color:var(--lx-paper);border-color:var(--lx-green-2)} /* patch 313 */")
must("stage filter",
'<option value="intalks">In talks</option><option value="ready">Ready to deal</option></select>',
'<option value="intalks">In talks</option><option value="meeting">Meeting set</option><option value="ready">Ready to deal</option></select>')

# ── 2. LinkedIn section markup ────────────────────────────────────────────────
must("linkedin section",
"""          <div id="or-today"></div>
        </div>""",
"""          <div id="or-today"></div>
        </div>

        <!-- LINKEDIN OUTREACH (patch 313) -->
        <div class="lx-section">
          <div class="lx-sechead"><h3>LinkedIn outreach</h3><span id="or-li-sub" style="font-size:14px;color:var(--lx-ink-2)"></span></div>
          <p class="lx-lede">Everyone you have messaged on LinkedIn, fed automatically by the draft agent. Move people along as they respond.</p>
          <div id="or-li-strip" style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:12px"></div>
          <div class="lx-tablewrap"><table class="lx-tbl"><thead><tr><th>Contact</th><th>Firm</th><th>Messaged</th><th>Stage</th><th style="min-width:300px">Move them along</th></tr></thead><tbody id="or-li-body"></tbody></table></div>
        </div>""")

# ── 3. template editor markup ─────────────────────────────────────────────────
must("template editor",
"""          <div id="or-email" style="display:none">
            <div class="lx-stats" id="or-estats\"""",
"""          <div id="or-email" style="display:none">
            <details style="margin-bottom:14px;border:1px solid var(--lx-line);background:var(--lx-white);padding:10px 14px"><summary style="cursor:pointer;font-weight:600">Email templates — intro, follow up, bump (click to edit)</summary>
              <div id="oz-tpl-editor" style="display:grid;gap:10px;margin-top:10px"></div>
              <button class="lx-btn" style="margin-top:8px" onclick="ozSaveTemplates()">Save templates</button>
            </details>
            <div class="lx-stats" id="or-estats\"""")

# ── 4. the JS: templates, smart email, LinkedIn panel ────────────────────────
must("js core",
"""function ozSentBadge(c){ return c.sentAt?'<span class="oz-sentbadge" title="Message sent '+ozEsc(c.sentAt)+'">&#10003; Sent '+ozEsc(c.sentAt)+'</span>':''; }""",
"""function ozSentBadge(c){ return c.sentAt?'<span class="oz-sentbadge" title="Message sent '+ozEsc(c.sentAt)+'">&#10003; Sent '+ozEsc(c.sentAt)+'</span>':''; }

// ── patch 313: templates + smart email + LinkedIn panel ─────────────────────
var OZ_BOOK_LINK='https://bookings.cloud.microsoft/bookwithme/user/a41e13f5915449d1bc15024d4c9a2987@krwmarketingsolutions.com/meetingtype/t26Ab5zztESUctqAbUGKoA2?bookingcode=6ab7cf76-c715-4034-9f76-473e9e1085ff&anonymous&ismsaljsauthenabled&ep=mcard';
var OZ_TPL_DEFAULT={
 intro:{s:'Quick intro from KRW Marketing Solutions',b:'Hi {{first_name}},\\n\\nKyler here, founder of KRW Marketing Solutions. We generate our own injury leads, consent verified and delivered in real time, and our intake team can sign the retainers so {{firm}} takes signed cases, not just leads.\\n\\nWorth 15 minutes? Grab a time here:\\n'+OZ_BOOK_LINK+'\\n\\nKyler'},
 follow:{s:'Following up, {{first_name}}',b:'Hi {{first_name}},\\n\\nCircling back in case my last note got buried. Short version: we generate our own injury leads and can deliver them as signed cases. If {{firm}} is taking on volume this quarter I would love 15 minutes.\\n\\n'+OZ_BOOK_LINK+'\\n\\nKyler'},
 bump:{s:'Last one from me, {{first_name}}',b:'Hi {{first_name}},\\n\\nLast one from me, I will keep it to one line. If new signed injury cases are interesting for {{firm}}, grab 15 minutes whenever works and I will show you exactly how we run it.\\n\\n'+OZ_BOOK_LINK+'\\n\\nKyler'},
 li_follow:{s:'',b:'Hey {{first_name}}, just floating this back up. Happy to show you how the signed case side works whenever you have 15 minutes. No pressure either way.\\n\\n'+OZ_BOOK_LINK}
};
var OZ_TPL={intro:null,follow:null,bump:null,li_follow:null};
function ozTplGet(k){ var t=OZ_TPL[k]; return (t&&t.b)?t:OZ_TPL_DEFAULT[k]; }
function ozLoadTemplates(){
  try{
    fetch(REV_API_URL+'/outreach/templates').then(function(r){return r.json();}).then(function(j){
      if(j&&j.ok&&j.templates){ for(var k in j.templates){ if(j.templates[k]&&j.templates[k].b)OZ_TPL[k]=j.templates[k]; } }
      ozRenderTplEditor();
    }).catch(function(){ozRenderTplEditor();});
  }catch(e){}
}
function ozRenderTplEditor(){
  var box=document.getElementById('oz-tpl-editor'); if(!box)return;
  function fld(k,label,hasSubj){ var t=ozTplGet(k);
    return '<div><div style="font-weight:600;margin-bottom:4px">'+label+'</div>'+
      (hasSubj?'<input id="tpl-s-'+k+'" style="width:100%;margin-bottom:4px;padding:6px;border:1px solid var(--lx-line)" value="'+ozEsc(t.s||'')+'">':'')+
      '<textarea id="tpl-b-'+k+'" rows="5" style="width:100%;padding:6px;border:1px solid var(--lx-line)">'+ozEsc(t.b||'')+'</textarea></div>'; }
  box.innerHTML=fld('intro','1st email — intro (subject, then body)',true)+fld('follow','2nd email — follow up',true)+fld('bump','3rd+ email — bump',true)+fld('li_follow','LinkedIn follow up (copied to clipboard, not emailed)',false)+
   '<div style="font-size:12px;color:var(--lx-ink-2)">Merge fields: {{first_name}} {{name}} {{firm}}</div>';
}
function ozSaveTemplates(){
  var out={};['intro','follow','bump','li_follow'].forEach(function(k){
    var s=document.getElementById('tpl-s-'+k), b=document.getElementById('tpl-b-'+k);
    out[k]={s:s?s.value:'',b:b?b.value:''}; if(out[k].b)OZ_TPL[k]=out[k];
  });
  fetch(REV_API_URL+'/outreach/templates',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({templates:out})})
    .then(function(r){return r.json();}).then(function(j){if(typeof showToast==='function')showToast(j&&j.ok?'Templates saved everywhere':'Save failed');})
    .catch(function(){if(typeof showToast==='function')showToast('Save failed');});
}
function ozTplFill(t,c){ var first=String(c.name||'').split(' ')[0]; return String(t||'').split('{{first_name}}').join(first).split('{{name}}').join(c.name||'').split('{{firm}}').join(c.company||'your firm'); }
function ozEmailSmart(id){
  var c=orData.find(function(x){return x.id===id;}); if(!c)return;
  var em=ozEmail(c); if(!em){ if(typeof showToast==='function')showToast('No email on file for '+c.name); return; }
  var n=c.emailsSent||0, key=n===0?'intro':(n===1?'follow':'bump');
  var t=ozTplGet(key);
  window.location.href='mailto:'+encodeURIComponent(em)+'?subject='+encodeURIComponent(ozTplFill(t.s||'',c))+'&body='+encodeURIComponent(ozTplFill(t.b||'',c));
  setTimeout(function(){ orMarkEmail(id,'sent'); },500);
}
function ozClip(t,msg){ try{ navigator.clipboard.writeText(t).then(function(){if(typeof showToast==='function')showToast(msg);},function(){window.prompt('Copy this:',t);}); }catch(e){ window.prompt('Copy this:',t); } }
function ozCopyLi(id){ var c=orData.find(function(x){return x.id===id;}); if(!c)return; if(!c.liMessage){if(typeof showToast==='function')showToast('No saved message for '+c.name);return;} ozClip(c.liMessage,c.name+' — message copied'); }
function ozCopyFollow(id){ var c=orData.find(function(x){return x.id===id;}); if(!c)return; ozClip(ozTplFill(ozTplGet('li_follow').b,c),c.name+' — follow up copied'); }
function ozSetStage(id,st){ var c=orData.find(function(x){return x.id===id;}); if(!c)return; c.stage=st; c.lastContact=ozToday(); c.followup=''; if(st==='meeting')c.meetingAt=ozToday(); orSave(); renderOutreach(); if(typeof showToast==='function')showToast(c.name+' → '+(STAGE_LABELS[st]||st)); }
function renderLinkedIn(){
  var strip=document.getElementById('or-li-strip'), tb=document.getElementById('or-li-body'); if(!strip||!tb)return;
  var li=orData.filter(function(c){return String(c.source||'')==='LinkedIn';});
  var adv=['responded','intalks','meeting','ready'];
  var messaged=li.filter(function(c){return c.sentAt||c.stage!=='cold';});
  var responded=li.filter(function(c){return adv.indexOf(c.stage)>-1;});
  var talks=li.filter(function(c){return c.stage==='intalks';});
  var meet=li.filter(function(c){return c.stage==='meeting'||c.stage==='ready';});
  var rate=messaged.length?Math.round(100*responded.length/messaged.length):0;
  function tile(n,l){return '<div style="background:var(--lx-white);border:1px solid var(--lx-line);padding:10px 6px;text-align:center"><div style="font-size:22px;font-weight:700">'+n+'</div><div style="font-size:10px;letter-spacing:1px;color:var(--lx-ink-2)">'+l+'</div></div>';}
  strip.innerHTML=tile(messaged.length,'MESSAGED')+tile(responded.length,'RESPONDED')+tile(talks.length,'IN TALKS')+tile(meet.length,'MEETINGS')+tile(rate+'%','RESPONSE RATE');
  var sub=document.getElementById('or-li-sub'); if(sub)sub.textContent=li.length?li.length+' contacts':'';
  var rows=li.slice().sort(function(a,b){return String(b.sentAt||b.liDraftAt||'').localeCompare(String(a.sentAt||a.liDraftAt||''));});
  tb.innerHTML=rows.map(function(c){
    var ds=c.sentAt?ozDays(c.sentAt):null;
    function sb(st,label){return c.stage===st?'<span class="oz-pill '+st+'">'+label+'</span>':'<button class="lx-btn quiet sm" onclick="ozSetStage('+c.id+',\\''+st+'\\')">'+label+'</button>';}
    return '<tr><td><span class="big" style="cursor:pointer" onclick="openContactModal('+c.id+')">'+ozEsc(c.name)+'</span></td>'+
      '<td>'+(c.company?ozEsc(c.company):'<span style="color:var(--lx-ink-3)">—</span>')+'</td>'+
      '<td>'+(c.sentAt?ozEsc(c.sentAt)+'<span class="sm">'+ds+'d ago</span>':(c.liDraftAt?'<span class="sm">draft ready</span>':'<span style="color:var(--lx-ink-3)">not yet</span>'))+'</td>'+
      '<td><span class="oz-pill '+c.stage+'">'+(STAGE_LABELS[c.stage]||c.stage)+'</span></td>'+
      '<td>'+(c.sentAt?'':'<button class="lx-btn quiet sm" onclick="ozMarkSent('+c.id+')">Mark sent</button> ')+
        sb('responded','Responded')+' '+sb('intalks','In talks')+' '+sb('meeting','Meeting set')+' '+
        (c.liMessage?'<button class="lx-btn quiet sm" onclick="ozCopyLi('+c.id+')">Copy message</button>':'')+
      '</td></tr>';
  }).join('')||'<tr><td colspan="5" class="lx-empty">No LinkedIn contacts yet. The draft agent adds them automatically when lawyers accept your connection.</td></tr>';
}
ozLoadTemplates();
// ── end patch 313 core ───────────────────────────────────────────────────────""")

# ── 5. smart Email button + follow-up copy in Needs you today ────────────────
must("needs-today email button",
"""        (em?'<a class="lx-btn quiet sm" href="mailto:'+ozEsc(em)+'" onclick="event.stopPropagation()">Email</a>':'')+""",
"""        (em?'<button class="lx-btn quiet sm" onclick="event.stopPropagation();ozEmailSmart('+c.id+')">Email</button>':'')+
        (it.li?'<button class="lx-btn quiet sm" onclick="event.stopPropagation();ozCopyFollow('+c.id+')">Copy follow up</button>':'')+""")

# ── 6. follow-up autopilot rule ───────────────────────────────────────────────
must("autopilot rule",
"""    if(ozStale(c)){ var d=ozDays(c.lastContact); items.push({c:c,rank:3+(100-Math.min(d,99))/1000,when:d+'d quiet',sub:c.lastContact,cls:''}); }""",
"""    // patch 313: LinkedIn follow-up autopilot - messaged 4+ days ago, no reply yet
    if(String(c.source||'')==='LinkedIn' && c.stage==='contacted' && c.sentAt){
      var dls=ozDays(c.sentAt);
      if(dls!==null && dls>=4){ items.push({c:c,rank:2.5,when:dls+'d no reply',sub:'LinkedIn follow up due',cls:'late',li:1}); return; }
    }
    if(ozStale(c)){ var d=ozDays(c.lastContact); items.push({c:c,rank:3+(100-Math.min(d,99))/1000,when:d+'d quiet',sub:c.lastContact,cls:''}); }""")

# ── 7. render hook ────────────────────────────────────────────────────────────
must("render hook",
"  renderOrStats(); renderOrToday();",
"  renderOrStats(); renderOrToday(); renderLinkedIn();   // patch 313")

# ── 8. build stamp ────────────────────────────────────────────────────────────
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
m = re.search(r"var KRW_BUILD = '([0-9-]+)';", src)
if not m: sys.exit("could not find KRW_BUILD - aborting")
src = src.replace(m.group(0), "var KRW_BUILD = '%s';" % stamp, 1)
open("version.txt", "w").write(stamp + chr(10))

shutil.copy2(TARGET, TARGET + ".pre-313.bak")
open(TARGET, "w", encoding="utf-8").write(src)
print("patch 313 applied. backup: index.html.pre-313.bak")
print("  build stamp -> " + stamp)
