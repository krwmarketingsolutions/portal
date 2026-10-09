#!/usr/bin/env python3
"""
patch-322.py  --  MVA Transfers box on Josh's LIVE portal (portal/ssdi.html)

The live SSDI portal Josh logs into is portal/ssdi.html (the standalone
ssdi-portal repo is empty / never deployed). This adds an "MVA Transfers"
card under his Postings card, visible only to Josh's logins, reading his
standalone KRW-JOSHUA-MVA line via /leads/feed and showing the real
disposition (disp_status/disp_note, exposed by patch 320).

Backup: ssdi.html.pre-322.bak    Safe to re-run: refuses twice.
"""
import os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
def find_root():
    for c in (HERE, os.path.dirname(HERE), os.getcwd(), os.path.dirname(os.getcwd())):
        if os.path.isfile(os.path.join(c, "portal", "ssdi.html")):
            return c
    return None
ROOT = find_root()
if not ROOT:
    sys.exit("could not find the krw folder (needs portal/ssdi.html) - run from ~/krw")
FILE = os.path.join(ROOT, "portal", "ssdi.html")

html = open(FILE, encoding="utf-8").read()
if "mva-card" in html or "patch 322" in html:
    sys.exit("patch 322 already applied to portal/ssdi.html - nothing to do")

def apply(s, anchor, replacement, what):
    n = s.count(anchor)
    if n != 1:
        sys.exit("ABORT (%s): anchor found %d times, expected exactly 1. No files changed." % (what, n))
    return s.replace(anchor, replacement, 1)

# ── 1. the card, inserted just before the "1696 Filed" (sec-signed) card ────
ANCHOR_CARD = ('    <div class="card">\n'
               '      <div class="card-hdr" onclick="toggleSection(\'sec-signed\')" style="cursor:pointer;user-select:none">')
CARD = (
    '    <!-- patch 322: MVA Transfers (Josh only) -->\n'
    '    <div class="card" id="mva-card" style="display:none">\n'
    '      <div class="card-hdr">\n'
    '        <div>\n'
    '          <div class="card-title">MVA Transfers</div>\n'
    '          <div class="card-sub">Live transfers routed to your intake team — status updates as they are worked</div>\n'
    '        </div>\n'
    '        <div class="filters">\n'
    '          <button class="rbtn" onclick="loadMvaTransfers()">↻</button>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div id="mva-load" class="st"><div class="spin"></div><div class="st-t">Loading your transfers...</div></div>\n'
    '      <div id="mva-empty" class="st" style="display:none"><div class="st-ico">\U0001f4e5</div><div class="st-t">No transfers yet</div><div class="st-s">Transfers will appear here as they come in</div></div>\n'
    '      <div id="mva-err" class="st" style="display:none"><div class="st-ico">⚠️</div><div class="st-t">Could not load transfers</div><div class="st-s" id="mva-err-msg"></div></div>\n'
    '      <div id="mvtbl-wrap" style="display:none;overflow-x:auto">\n'
    '        <table>\n'
    '          <thead><tr>\n'
    '            <th>Date</th><th>Name</th><th>Phone</th><th>State</th><th>Status</th>\n'
    '          </tr></thead>\n'
    '          <tbody id="mvtbl"></tbody>\n'
    '        </table>\n'
    '      </div>\n'
    '    </div>\n\n'
)
html = apply(html, ANCHOR_CARD, CARD + ANCHOR_CARD, "insert MVA card")

# ── 2. fire the loader from showPortal ──────────────────────────────────────
ANCHOR_SHOW = "  setTimeout(loadLeads, 100);"
html = apply(html, ANCHOR_SHOW, ANCHOR_SHOW + "\n  setTimeout(loadMvaTransfers, 100);", "showPortal loader")

# ── 3. the loader, inserted before </script> ────────────────────────────────
ANCHOR_END = "function closeSettings(){ document.getElementById('settings-modal').classList.remove('open'); }\n</script>"
FUNC = (
    "function closeSettings(){ document.getElementById('settings-modal').classList.remove('open'); }\n"
    "// patch 322: MVA Transfers box. Reads Josh's standalone KRW-JOSHUA-MVA line only,\n"
    "// so it never mixes with the SSDI sections. Shown only for Josh's logins.\n"
    "var JOSH_MVA_IDS = ['SSDI-AZ-1696','SSDI-SLC-1696','KRW-JOSHUA-SIGNED','KRW-JOSHUA-CKX'];\n"
    "function loadMvaTransfers(){\n"
    "  if (!S) return;\n"
    "  var pid = String(S.pub_id || '').toUpperCase();\n"
    "  if (JOSH_MVA_IDS.map(function(x){return x.toUpperCase();}).indexOf(pid) === -1) return;\n"
    "  var card = document.getElementById('mva-card'); if (card) card.style.display = '';\n"
    "  document.getElementById('mva-load').style.display  = '';\n"
    "  document.getElementById('mva-empty').style.display = 'none';\n"
    "  document.getElementById('mva-err').style.display   = 'none';\n"
    "  document.getElementById('mvtbl-wrap').style.display = 'none';\n"
    "  var url = API + '/leads/feed?portal_id=KRW-JOSHUA-MVA&days=9999&limit=5000&api_key=' + API_KEY;\n"
    "  fetch(url)\n"
    "  .then(function(r){ return r.json(); })\n"
    "  .then(function(d){\n"
    "    if (!d.ok) throw new Error(d.error || 'Server error');\n"
    "    var leads = d.leads || [];\n"
    "    document.getElementById('mva-load').style.display = 'none';\n"
    "    if (!leads.length) { document.getElementById('mva-empty').style.display = ''; return; }\n"
    "    leads.sort(function(a,b){ return new Date(b.received_at||0) - new Date(a.received_at||0); });\n"
    "    var tbody = document.getElementById('mvtbl');\n"
    "    tbody.innerHTML = '';\n"
    "    leads.forEach(function(l){\n"
    "      var dateObj = l.received_at ? new Date(l.received_at) : null;\n"
    "      var date = dateObj\n"
    "        ? dateObj.toLocaleDateString('en-US', {month:'2-digit',day:'2-digit',year:'numeric'}) +\n"
    "          ' <span style=\"color:var(--ink-3);font-size:11px\">' + dateObj.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',hour12:true,timeZone:'America/New_York'}) + '</span>'\n"
    "        : '—';\n"
    "      var name = ((l.first_name||'') + ' ' + (l.last_name||'')).trim() || '—';\n"
    "      var disp = l.disp_status || l.status || 'Pending';\n"
    "      var note = l.disp_note || '';\n"
    "      var sl = String(disp).toLowerCase();\n"
    "      var badge = sl.indexOf('sign') === 0 || sl.indexOf('accept') === 0 || sl === 'retained'\n"
    "        ? '<span class=\"badge b-cpa\">✓ ' + disp + '</span>'\n"
    "        : sl.indexOf('reject') === 0\n"
    "        ? '<span class=\"badge b-no\">' + disp + '</span>'\n"
    "        : '<span class=\"badge b-pending\">⏳ ' + disp + '</span>';\n"
    "      var noteHtml = note ? '<div style=\"color:var(--ink-3);font-size:11px;margin-top:2px\">' + note + '</div>' : '';\n"
    "      var tr = document.createElement('tr');\n"
    "      tr.innerHTML =\n"
    "        '<td>' + date + '</td>' +\n"
    "        '<td style=\"font-weight:500\">' + name + '</td>' +\n"
    "        '<td style=\"font-family:monospace;font-size:12px;color:var(--ink-3)\">' + (l.phone || '—') + '</td>' +\n"
    "        '<td>' + (l.state || '—') + '</td>' +\n"
    "        '<td>' + badge + noteHtml + '</td>';\n"
    "      tbody.appendChild(tr);\n"
    "    });\n"
    "    document.getElementById('mvtbl-wrap').style.display = '';\n"
    "  })\n"
    "  .catch(function(e){\n"
    "    document.getElementById('mva-load').style.display = 'none';\n"
    "    document.getElementById('mva-err').style.display  = '';\n"
    "    document.getElementById('mva-err-msg').textContent = e.message;\n"
    "  });\n"
    "}\n"
    "</script>"
)
html = apply(html, ANCHOR_END, FUNC, "loadMvaTransfers function")

shutil.copyfile(FILE, FILE + ".pre-322.bak")
open(FILE, "w", encoding="utf-8").write(html)
print("patch 322 applied to", FILE)
