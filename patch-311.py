#!/usr/bin/env python3
"""
patch-311.py  --  "Sent" button on the Outreach board (Kyler, Oct 7)

WHAT IT ADDS (portal/index.html)
  A one-tap "Sent" button next to each contact so Kyler can mark that he
  actually fired off the outreach message (LinkedIn DM, email, whatever):
    - board cards: small "Mark sent" button under the name; once pressed the
      card shows a green "Sent <date>" badge instead
    - list view: a "Sent" button beside the existing "Touch" button, same
      swap to a badge once pressed
    - "Needs you today": a "Sent the message" action beside "Logged a touch"
  Pressing it stamps sentAt + lastContact with today, moves a cold contact to
  Contacted, sets a 4 day follow-up if none exists, and syncs to the server
  like every other board edit.

  Also bumps the build stamp so open tabs and the phone PWA pick the change
  up on their own (patch 297 self-update).

Usage (from ~/krw/portal):
    python3 patch-311.py
    git add -A && git commit -m "patch 311: Sent button on outreach" && git push

Backup: index.html.pre-311.bak. Safe to re-run.
"""
import os, re, shutil, sys, datetime

TARGET = "index.html"
if not os.path.exists(TARGET):
    sys.exit("index.html not found - run this from ~/krw/portal")

src = open(TARGET, encoding="utf-8").read()
if "patch 311" in src:
    sys.exit("patch 311 already applied - nothing to do")

def must_replace(label, old, new):
    global src
    n = src.count(old)
    if n != 1:
        sys.exit("%s: expected exactly 1 match, found %d - aborting, index.html untouched" % (label, n))
    src = src.replace(old, new, 1)

# ── 1. the function ──────────────────────────────────────────────────────────
must_replace("ozSnooze anchor",
"""function ozSnooze(id,days){
  var c=orData.find(function(x){return x.id===id;}); if(!c)return;
  c.followup=new Date(Date.now()+days*86400000).toISOString().split('T')[0];
  orSave(); renderOutreach(); if(typeof showToast==='function')showToast(c.name+' — snoozed '+days+' days');
}""",
"""function ozSnooze(id,days){
  var c=orData.find(function(x){return x.id===id;}); if(!c)return;
  c.followup=new Date(Date.now()+days*86400000).toISOString().split('T')[0];
  orSave(); renderOutreach(); if(typeof showToast==='function')showToast(c.name+' — snoozed '+days+' days');
}
// patch 311: one tap to say "I actually sent them the message"
function ozMarkSent(id){
  var c=orData.find(function(x){return x.id===id;}); if(!c)return;
  c.sentAt=ozToday(); c.lastContact=ozToday();
  if(c.stage==='cold')c.stage='contacted';
  if(!c.followup)c.followup=new Date(Date.now()+4*86400000).toISOString().split('T')[0];
  orSave(); renderOutreach(); if(typeof showToast==='function')showToast(c.name+' — marked sent');
}
function ozSentBadge(c){ return c.sentAt?'<span class="oz-sentbadge" title="Message sent '+ozEsc(c.sentAt)+'">&#10003; Sent '+ozEsc(c.sentAt)+'</span>':''; }""")

# ── 2. badge style ───────────────────────────────────────────────────────────
must_replace("stage pill css anchor",
"""  .stage-pill.cold{background:var(--subtle);color:var(--muted);border:1px solid var(--border)}""",
"""  .stage-pill.cold{background:var(--subtle);color:var(--muted);border:1px solid var(--border)}
  .oz-sentbadge{display:inline-block;font-size:11.5px;font-weight:600;color:#1f4d36;background:#eef7eb;border:1px solid #bcd9bc;border-radius:999px;padding:1px 9px;white-space:nowrap} /* patch 311 */""")

# ── 3. board card: button under the name, badge once sent ────────────────────
must_replace("board card name",
"""      card.innerHTML='<button class="x" title="Delete" onclick="event.stopPropagation();deleteContact('+c.id+')">×</button>'+
        '<div class="nm">'+ozEsc(c.name)+'</div>'+""",
"""      card.innerHTML='<button class="x" title="Delete" onclick="event.stopPropagation();deleteContact('+c.id+')">×</button>'+
        '<div class="nm">'+ozEsc(c.name)+' '+(c.sentAt?ozSentBadge(c):'<button class="lx-btn quiet sm" style="padding:1px 8px;font-size:11px" onclick="event.stopPropagation();ozMarkSent('+c.id+')">Mark sent</button>')+'</div>'+""")

# ── 4. list view: Sent button (or badge) beside Touch ────────────────────────
must_replace("list row actions",
"""      '<td><button class="lx-btn quiet sm" onclick="event.stopPropagation();ozTouch('+c.id+')">Touch</button></td>';""",
"""      '<td>'+(c.sentAt?ozSentBadge(c):'<button class="lx-btn quiet sm" onclick="event.stopPropagation();ozMarkSent('+c.id+')">Sent</button>')+' <button class="lx-btn quiet sm" onclick="event.stopPropagation();ozTouch('+c.id+')">Touch</button></td>';""")

# ── 5. Needs you today: Sent action ──────────────────────────────────────────
must_replace("needs-today actions",
"""        '<button class="lx-btn quiet sm" onclick="event.stopPropagation();ozTouch('+c.id+')">Logged a touch</button>'+""",
"""        (c.sentAt?ozSentBadge(c):'<button class="lx-btn quiet sm" onclick="event.stopPropagation();ozMarkSent('+c.id+')">Sent the message</button>')+
        '<button class="lx-btn quiet sm" onclick="event.stopPropagation();ozTouch('+c.id+')">Logged a touch</button>'+""")

# ── 6. bump the self-update stamp ────────────────────────────────────────────
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
m = re.search(r"var KRW_BUILD = '([0-9-]+)';", src)
if not m:
    sys.exit("could not find KRW_BUILD - aborting")
src = src.replace(m.group(0), "var KRW_BUILD = '%s';" % stamp, 1)
open("version.txt", "w").write(stamp + chr(10))

shutil.copy2(TARGET, TARGET + ".pre-311.bak")
open(TARGET, "w", encoding="utf-8").write(src)
print("patch 311 applied. backup: index.html.pre-311.bak")
print("  Mark sent button on board cards, list rows and Needs you today")
print("  build stamp -> " + stamp + " (open tabs self-update)")
