#!/usr/bin/env python3
"""
patch-316.py  --  Intro email A/B test: rotate variants, score by replies

HOW IT WORKS (Kyler, Oct 7: "test between A and D")
  - A contact's FIRST email now alternates between Intro A and Intro D.
    The rotation keeps the two groups balanced, and each contact is stamped
    with the variant they received (introVariant), permanently.
  - A reply (caught by the reply watcher) or any stage advance counts as a
    response for that contact's variant.
  - The Email view shows the scoreboard: sent, replies and response rate per
    variant, updating live. When one clearly wins, make it the only intro by
    blanking the loser in the template editor.
  - The template editor edits both variants (Intro A / Intro D) plus the
    follow up, bump and LinkedIn texts as before.

Usage (from ~/krw/portal):
    python3 patch-316.py
"""
import os, re, shutil, sys, datetime

TARGET = "index.html"
if not os.path.exists(TARGET):
    sys.exit("index.html not found")
src = open(TARGET, encoding="utf-8").read()
if "patch 316" in src:
    sys.exit("patch 316 already applied - nothing to do")

def must(label, old, new):
    global src
    n = src.count(old)
    if n != 1:
        sys.exit("%s: expected 1 match, found %d - aborting" % (label, n))
    src = src.replace(old, new, 1)

# ── 1. scoreboard div after the template editor ───────────────────────────────
must("ab scoreboard div",
"""              <button class="lx-btn" style="margin-top:8px" onclick="ozSaveTemplates()">Save templates</button>
            </details>""",
"""              <button class="lx-btn" style="margin-top:8px" onclick="ozSaveTemplates()">Save templates</button>
            </details>
            <div id="oz-ab" style="margin-bottom:14px"></div>""")

# ── 2. variant pick inside ozEmailSmart ───────────────────────────────────────
must("smart email variant pick",
"""  var n=c.emailsSent||0, key=n===0?'intro':(n===1?'follow':'bump');
  var t=ozTplGet(key);""",
"""  var n=c.emailsSent||0, key;
  if(n===0){
    // patch 316: A/B rotation on the first touch, balanced across contacts
    if(!c.introVariant) c.introVariant=ozPickIntroVariant();
    key=c.introVariant==='A'?'intro_a':'intro_d';
    if(!ozTplGet(key)||!ozTplGet(key).b) key='intro';
  } else key=(n===1?'follow':'bump');
  var t=ozTplGet(key);""")

# ── 3. the A/B machinery + scoreboard renderer ────────────────────────────────
must("ab machinery",
"""ozLoadTemplates();
// ── end patch 313 core ───────────────────────────────────────────────────────""",
"""// ── patch 316: intro A/B test ────────────────────────────────────────────────
function ozPickIntroVariant(){
  var a=0,d=0;
  orData.forEach(function(c){ if(c.introVariant==='A')a++; else if(c.introVariant==='D')d++; });
  if(a===d) return Math.random()<0.5?'A':'D';
  return a<d?'A':'D';
}
function ozAbResponded(c){ return c.emailStatus==='replied'||['responded','intalks','meeting','ready'].indexOf(c.stage)>-1; }
function ozRenderAb(){
  var box=document.getElementById('oz-ab'); if(!box)return;
  var st={A:{s:0,r:0},D:{s:0,r:0}};
  orData.forEach(function(c){ var v=c.introVariant; if(!st[v])return; st[v].s++; if(ozAbResponded(c))st[v].r++; });
  if(!st.A.s&&!st.D.s){ box.innerHTML='<div style="font-size:13px;color:var(--lx-ink-2);border:1px dashed var(--lx-line);padding:10px 14px">Intro A/B test armed. First emails rotate between Intro A and Intro D automatically; replies score here.</div>'; return; }
  function cell(v,o){ var rate=o.s?Math.round(100*o.r/o.s):0;
    return '<div style="flex:1;background:var(--lx-white);border:1px solid var(--lx-line);padding:10px 14px"><b>Intro '+v+'</b><div style="font-size:13px;color:var(--lx-ink-2)">'+o.s+' sent · '+o.r+' repl'+(o.r===1?'y':'ies')+' · <b>'+rate+'%</b></div></div>'; }
  var lead=''; if(st.A.s>=5&&st.D.s>=5){ var ra=st.A.r/st.A.s, rd=st.D.r/st.D.s; if(ra!==rd) lead='<div style="font-size:12px;color:var(--lx-green-2);margin-top:4px">Intro '+(ra>rd?'A':'D')+' is leading</div>'; }
  box.innerHTML='<div style="display:flex;gap:8px">'+cell('A',st.A)+cell('D',st.D)+'</div>'+lead;
}
ozLoadTemplates();
// ── end patch 313 core ───────────────────────────────────────────────────────""")

# ── 4. editor shows both variants ─────────────────────────────────────────────
must("editor fields",
"""  box.innerHTML=fld('intro','1st email — intro (subject, then body)',true)+fld('follow','2nd email — follow up',true)+fld('bump','3rd+ email — bump',true)+fld('li_follow','LinkedIn follow up (copied to clipboard, not emailed)',false)+""",
"""  box.innerHTML=fld('intro_a','1st email — INTRO A (in the A/B test)',true)+fld('intro_d','1st email — INTRO D (in the A/B test)',true)+fld('follow','2nd email — follow up',true)+fld('bump','3rd+ email — bump',true)+fld('li_follow','LinkedIn follow up (copied to clipboard, not emailed)',false)+""")

must("save keys",
"""  var out={};['intro','follow','bump','li_follow'].forEach(function(k){""",
"""  var out={};['intro','intro_a','intro_d','follow','bump','li_follow'].forEach(function(k){""")

# ── 5. render hook ────────────────────────────────────────────────────────────
must("render hook",
"  renderOrStats(); renderOrToday(); renderLinkedIn();   // patch 313",
"  renderOrStats(); renderOrToday(); renderLinkedIn(); if(typeof ozRenderAb==='function')ozRenderAb();   // patch 313/316")

# ── 6. defaults for the variants ──────────────────────────────────────────────
must("variant defaults",
""" li_follow:{s:'',b:'Hey {{first_name}}, just floating this back up.""",
""" intro_a:{s:'Signed MVA cases for {{firm}}',b:'Hi {{first_name}},\\n\\nKyler here, founder of KRW Marketing Solutions. Quick version: we generate our own MVA leads, and our intake professionals work them and sign the retainer for you. What lands on your desk is a fully signed car accident case, not a list of numbers to chase.\\n\\nLive transfers or signed packets, whatever fits how {{firm}} runs intake. Worth 15 minutes?\\n'+OZ_BOOK_LINK+'\\n\\nKyler'},
 intro_d:{s:'Fully signed MVA cases, no chasing',b:'Hi {{first_name}},\\n\\nOne sentence pitch: we generate MVA leads with our own ads, our intake team signs the retainer, and {{firm}} gets a finished car accident case by transfer or packet instead of a phone number that never answers.\\n\\nIf that is interesting, grab 15 minutes here:\\n'+OZ_BOOK_LINK+'\\n\\nKyler'},
 li_follow:{s:'',b:'Hey {{first_name}}, just floating this back up.""")

# ── 7. build stamp ────────────────────────────────────────────────────────────
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
m = re.search(r"var KRW_BUILD = '([0-9-]+)';", src)
if not m: sys.exit("KRW_BUILD not found")
src = src.replace(m.group(0), "var KRW_BUILD = '%s';" % stamp, 1)
open("version.txt", "w").write(stamp + chr(10))

shutil.copy2(TARGET, TARGET + ".pre-316.bak")
open(TARGET, "w", encoding="utf-8").write(src)
print("patch 316 applied, build " + stamp)
