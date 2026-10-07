#!/usr/bin/env python3
"""
patch-286.py  --  Outreach page rebuilt in the Leads-page (retainer) look
                  + paste-a-list law-firm importer

Applies to portal/index.html. Three changes, all additive or scoped to the
Outreach page - no other page is touched:

  1. CSS  : #page-outreach joins the retainer palette (paper/green, Source Serif),
            plus new oz- classes for the work queue, board, and sequence table.
  2. HTML : the whole #page-outreach block is replaced with a new layout -
            Summary stats (clickable filters), "Needs you today" work queue,
            Pipeline (board / table), and Email sequence section.
  3. JS   : new render functions appended at the end of the dashboard script.
            JS function declarations let the last definition win, so the old
            renderOutreach/renderBoard/renderList/renderEmailTab/renderOrStats/
            setOrView/getFiltered are overridden without deleting them.
            Contact data, orSave/orPush/orFetch and the edit modal are untouched.

  New: "Paste a list" button -> paste law firms as CSV, TSV, or free text.
       The parser pulls out firm, contact name, email, phone, state and
       website per line, shows an editable preview, skips duplicates by email
       or firm name, and imports the rest as Cold contacts.

Usage (from ~/krw/portal):
    python3 patch-286.py
    # open index.html in a browser, click Outreach, check it
    git add -A && git commit -m "patch 286: outreach page rebuild + firm importer" && git push

Backup written to index.html.pre-286.bak. Safe to re-run: refuses to apply twice.
"""
import os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "index.html")
if not os.path.exists(TARGET):
    TARGET = os.path.join(os.getcwd(), "index.html")
if not os.path.exists(TARGET):
    sys.exit("index.html not found - run this from ~/krw/portal")

src = open(TARGET, encoding="utf-8").read()
if "patch 286" in src:
    sys.exit("patch 286 already applied - nothing to do")

# ──────────────────────────────────────────────────────────────────────────────
# 1. CSS
# ──────────────────────────────────────────────────────────────────────────────
CSS = r'''
  /* ══ OUTREACH PAGE (patch 286 — retainer look, matches Leads) ═════════════ */
  #page-outreach{
    --lx-paper:#F3EEE3; --lx-paper-2:#EAE3D3; --lx-ink:#1E2A22; --lx-ink-2:#4E5A52; --lx-ink-3:#8A9089;
    --lx-green:#1F4D36; --lx-green-2:#2E6B4B; --lx-green-soft:#D9E4DB; --lx-brown:#8C6A44; --lx-brown-soft:#E7D9C5;
    --lx-red:#8E3B2F; --lx-red-soft:#EDD3CC; --lx-line:#CFC5B0; --lx-line-2:#B9AE95; --lx-white:#FBF8F1;
    background:var(--lx-paper); color:var(--lx-ink);
    font-family:"Source Serif 4", Georgia, "Times New Roman", serif;
    font-variant-numeric:tabular-nums;
  }
  #page-outreach .header-bar{background:var(--lx-paper);border-bottom:2px solid var(--lx-green);padding:26px 40px 18px;align-items:flex-end}
  #page-outreach .header-bar-left h2{font-family:inherit;font-size:34px;font-weight:600;letter-spacing:-0.01em;line-height:1.1}
  #page-outreach .header-bar-left p{font-family:inherit;font-size:15px;color:var(--lx-ink-2);margin-top:6px;max-width:64ch}
  #page-outreach .header-bar-right{gap:14px}
  #page-outreach button:focus-visible, #page-outreach input:focus-visible, #page-outreach select:focus-visible, #page-outreach textarea:focus-visible{outline:2px solid var(--lx-green);outline-offset:2px}

  /* work queue */
  .oz-queue{list-style:none;margin:0;padding:0;border:1px solid var(--lx-line);background:var(--lx-white)}
  .oz-queue li{display:grid;grid-template-columns:118px 1fr auto;gap:14px;padding:11px 16px;border-bottom:1px solid var(--lx-line);align-items:center}
  @media(max-width:760px){.oz-queue li{grid-template-columns:1fr;gap:7px}.oz-when{text-align:left}.oz-do{justify-content:flex-start}}
  .oz-queue li:last-child{border-bottom:0}
  .oz-queue li:hover{background:var(--lx-paper)}
  .oz-when{font-size:13px;font-weight:600;color:var(--lx-brown);text-align:right;line-height:1.25}
  .oz-when.late{color:var(--lx-red)}
  .oz-when.now{color:var(--lx-green-2)}
  .oz-when small{display:block;font-size:11.5px;font-weight:400;color:var(--lx-ink-3)}
  .oz-who{min-width:0;cursor:pointer}
  .oz-who b{font-weight:600;font-size:15px}
  .oz-who .sub{display:block;font-size:13px;color:var(--lx-ink-3);line-height:1.35;word-break:break-word}
  .oz-do{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}
  .oz-calm{padding:26px 16px;text-align:center;color:var(--lx-ink-3);font-size:14.5px;border:1px solid var(--lx-line);background:var(--lx-white)}
  .oz-calm b{color:var(--lx-green);font-weight:600}

  /* board */
  .oz-board{display:grid;grid-template-columns:repeat(5,minmax(190px,1fr));gap:14px;align-items:start}
  @media(max-width:1150px){.oz-board{grid-template-columns:repeat(2,1fr)}}
  @media(max-width:620px){.oz-board{grid-template-columns:1fr}}
  .oz-col{background:var(--lx-white);border:1px solid var(--lx-line);border-top:3px solid var(--lx-line-2);min-height:120px;display:flex;flex-direction:column}
  .oz-col[data-stage="contacted"]{border-top-color:var(--lx-brown)}
  .oz-col[data-stage="responded"]{border-top-color:var(--lx-brown)}
  .oz-col[data-stage="intalks"]{border-top-color:var(--lx-green-2)}
  .oz-col[data-stage="ready"]{border-top-color:var(--lx-green)}
  .oz-col.drop{background:var(--lx-green-soft)}
  .oz-colhd{display:flex;align-items:baseline;justify-content:space-between;gap:8px;padding:10px 13px;border-bottom:1px solid var(--lx-line)}
  .oz-colhd h4{font-size:15px;font-weight:600;margin:0}
  .oz-colhd .n{font-size:13px;color:var(--lx-ink-3)}
  .oz-colbody{padding:10px;display:flex;flex-direction:column;gap:9px;flex:1}
  .oz-card{background:var(--lx-paper);border:1px solid var(--lx-line);padding:9px 11px;cursor:pointer;position:relative;transition:border-color .15s}
  .oz-card:hover{border-color:var(--lx-green)}
  .oz-card.dragging{opacity:.45}
  .oz-card .nm{font-weight:600;font-size:14.5px;line-height:1.25;padding-right:14px}
  .oz-card .co{font-size:13px;color:var(--lx-ink-2);line-height:1.3;margin-top:1px;word-break:break-word}
  .oz-card .em{font-size:12.5px;color:var(--lx-green-2);margin-top:3px;word-break:break-all}
  .oz-card .ft{display:flex;justify-content:space-between;gap:8px;margin-top:6px;font-size:12px;color:var(--lx-ink-3)}
  .oz-card .ft .late{color:var(--lx-red);font-weight:600}
  .oz-card .x{position:absolute;top:4px;right:5px;opacity:0;background:none;border:0;color:var(--lx-red);font-size:15px;line-height:1;cursor:pointer;padding:1px 4px}
  .oz-card:hover .x{opacity:1}
  .oz-empty{padding:16px 8px;text-align:center;color:var(--lx-ink-3);font-size:13px}

  /* pills */
  .oz-pill{display:inline-block;font-size:12.5px;padding:1px 8px;border-radius:2px;white-space:nowrap;border:1px solid var(--lx-line-2);color:var(--lx-ink-2);background:transparent}
  .oz-pill.cold{color:var(--lx-ink-3)}
  .oz-pill.contacted{background:var(--lx-brown-soft);color:var(--lx-brown);border-color:var(--lx-brown-soft)}
  .oz-pill.responded{background:var(--lx-brown-soft);color:var(--lx-brown);border-color:var(--lx-brown)}
  .oz-pill.intalks{background:var(--lx-green-soft);color:var(--lx-green-2);border-color:#C4D3C8}
  .oz-pill.ready{background:var(--lx-green);color:var(--lx-paper);border-color:var(--lx-green)}
  .oz-pill.seq{background:var(--lx-paper-2);color:var(--lx-ink-2);border-color:var(--lx-line)}
  .oz-pill.rep{background:var(--lx-green-soft);color:var(--lx-green);border-color:#C4D3C8}
  .oz-pill.meet{background:var(--lx-green);color:var(--lx-paper);border-color:var(--lx-green)}

  /* import modal */
  .oz-shade{position:fixed;inset:0;background:rgba(30,42,34,.32);z-index:870;display:none;align-items:flex-start;justify-content:center;padding:40px 16px;overflow-y:auto}
  .oz-shade.open{display:flex}
  .oz-modal{background:#F3EEE3;color:#1E2A22;border:1px solid #B9AE95;box-shadow:0 18px 50px rgba(30,42,34,.22);width:980px;max-width:100%;
    font-family:"Source Serif 4", Georgia, "Times New Roman", serif;font-variant-numeric:tabular-nums;
    --lx-paper:#F3EEE3; --lx-paper-2:#EAE3D3; --lx-ink:#1E2A22; --lx-ink-2:#4E5A52; --lx-ink-3:#8A9089;
    --lx-green:#1F4D36; --lx-green-2:#2E6B4B; --lx-green-soft:#D9E4DB; --lx-brown:#8C6A44; --lx-brown-soft:#E7D9C5;
    --lx-red:#8E3B2F; --lx-red-soft:#EDD3CC; --lx-line:#CFC5B0; --lx-line-2:#B9AE95; --lx-white:#FBF8F1}
  .oz-mhd{padding:20px 26px 14px;border-bottom:2px solid var(--lx-green);display:flex;justify-content:space-between;align-items:flex-start;gap:14px}
  .oz-mhd h3{font-size:24px;font-weight:600;margin:0}
  .oz-mhd p{font-size:14px;color:var(--lx-ink-2);margin:5px 0 0;max-width:72ch}
  .oz-mbody{padding:18px 26px 24px}
  .oz-ta{font:inherit;font-size:14px;width:100%;min-height:170px;background:var(--lx-white);border:1px solid var(--lx-line-2);border-radius:3px;padding:11px 13px;color:var(--lx-ink);line-height:1.5;resize:vertical}
  .oz-mrow{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:13px}
  .oz-mfoot{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;margin-top:16px;padding-top:14px;border-top:1px solid var(--lx-line)}
  .oz-prev{max-height:330px;overflow:auto;border:1px solid var(--lx-line);background:var(--lx-white);margin-top:14px}
  .oz-prev table{border-collapse:collapse;width:100%;font-size:13.5px}
  .oz-prev table{table-layout:fixed}
  .oz-prev th,.oz-prev td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--lx-line);vertical-align:middle;overflow:hidden}
  .oz-prev th:nth-child(2),.oz-prev td:nth-child(2){width:23%}
  .oz-prev th:nth-child(3),.oz-prev td:nth-child(3){width:16%}
  .oz-prev th:nth-child(4),.oz-prev td:nth-child(4){width:27%}
  .oz-prev th:nth-child(5),.oz-prev td:nth-child(5){width:15%}
  .oz-prev th:nth-child(6),.oz-prev td:nth-child(6){width:7%}
  .oz-prev th:nth-child(7),.oz-prev td:nth-child(7){width:11%;white-space:nowrap}
  .oz-prev th{position:sticky;top:0;background:var(--lx-white);font-weight:600;font-size:13px;color:var(--lx-ink-2);border-bottom:2px solid var(--lx-line-2);z-index:2}
  .oz-prev tr.dup td{background:var(--lx-brown-soft);color:var(--lx-ink-2)}
  .oz-prev tr.skip td{opacity:.45;text-decoration:line-through}
  .oz-prev input{font:inherit;font-size:13.5px;background:transparent;border:0;border-bottom:1px dashed var(--lx-line-2);padding:1px 2px;width:100%;color:inherit}
  .oz-prev input:focus{background:var(--lx-paper);outline:none;border-bottom-color:var(--lx-green)}
  .oz-note{font-size:13.5px;color:var(--lx-ink-2)}
  .oz-note b{color:var(--lx-ink)}
  .oz-warn{font-size:13.5px;color:var(--lx-red)}
'''

if src.count("</style>") < 1:
    sys.exit("no </style> found - aborting")
src = src.replace("</style>", CSS + "\n</style>", 1)

# ──────────────────────────────────────────────────────────────────────────────
# 2. HTML - replace the whole #page-outreach block
# ──────────────────────────────────────────────────────────────────────────────
HTML = r'''    <!-- ═══ OUTREACH PAGE (rebuilt in patch 286) ═══ -->
    <div class="page" id="page-outreach" style="display:none">
      <div class="header-bar">
        <div class="header-bar-left">
          <h2>Outreach</h2>
          <p>Every firm and contact you are working, from first touch to signed deal. Click any card or row to open the full record.</p>
        </div>
        <div class="header-bar-right">
          <span class="lx-live" id="or-live"><i></i><span id="or-live-txt">Loading</span></span>
          <button class="lx-btn quiet" onclick="ozOpenImport()">Paste a list</button>
          <button class="lx-btn" onclick="openContactModal(null)">+ Contact</button>
        </div>
      </div>

      <div class="lx-body">

        <!-- SUMMARY -->
        <div class="lx-section">
          <div class="lx-sechead"><h3>Summary</h3><span class="lx-latest" id="or-sum-note"></span></div>
          <div class="lx-stats" id="or-stats"></div>
          <div class="lx-stathint">Click a card to filter the pipeline below to just those contacts. Click it again to clear.</div>
        </div>

        <!-- WORK QUEUE -->
        <div class="lx-section">
          <div class="lx-sechead"><h3>Needs you today</h3><span id="or-today-sub" style="font-size:14px;color:var(--lx-ink-2)"></span></div>
          <p class="lx-lede">Follow-ups that are due or overdue, replies waiting on an answer, and anyone contacted but left untouched for a week. Worked top to bottom, this is the day's list.</p>
          <div id="or-today"></div>
        </div>

        <!-- PIPELINE -->
        <div class="lx-section">
          <h3>Pipeline</h3>
          <p class="lx-lede">Drag a card between columns on the board to move someone along, or switch to the table for sorting and a wider view.</p>
          <div class="lx-tools">
            <input class="lx-search" id="or-search" type="search" placeholder="Search name, firm, email, state" oninput="renderOutreach()">
            <div class="lx-seg" id="or-viewseg">
              <button id="vbtn-board" aria-pressed="true" onclick="setOrView('board')">Board</button>
              <button id="vbtn-list" aria-pressed="false" onclick="setOrView('list')">Table</button>
              <button id="vbtn-email" aria-pressed="false" onclick="setOrView('email')">Email</button>
            </div>
            <select class="lx-winsel" id="or-role" onchange="renderOutreach()"><option value="">Every role</option><option value="buyer">Buyers</option><option value="seller">Sellers</option><option value="both">Both</option></select>
            <select class="lx-winsel" id="or-vert" onchange="renderOutreach()"><option value="">Every vertical</option><option value="MVA">MVA</option><option value="SSDI">SSDI</option><option value="OTHER">Other</option></select>
            <select class="lx-winsel" id="or-stage" onchange="renderOutreach()"><option value="">Every stage</option><option value="cold">Cold</option><option value="contacted">Contacted</option><option value="responded">Responded</option><option value="intalks">In talks</option><option value="ready">Ready to deal</option></select>
            <div class="lx-meta"><span id="or-count">—</span></div>
          </div>

          <div id="or-board" class="oz-board"></div>

          <div id="or-list" style="display:none">
            <div class="lx-tablewrap">
              <table class="lx-tbl">
                <thead><tr>
                  <th class="sortable" data-key="name" onclick="ozSort('name')">Contact</th>
                  <th class="sortable" data-key="company" onclick="ozSort('company')">Firm</th>
                  <th>Reach</th>
                  <th class="sortable" data-key="state" onclick="ozSort('state')">State</th>
                  <th class="sortable" data-key="vertical" onclick="ozSort('vertical')">Vertical</th>
                  <th class="sortable" data-key="stage" onclick="ozSort('stage')">Stage</th>
                  <th class="sortable" data-key="lastContact" onclick="ozSort('lastContact')">Last touch</th>
                  <th class="sortable" data-key="followup" onclick="ozSort('followup')">Follow-up</th>
                  <th></th>
                </tr></thead>
                <tbody id="or-list-body"></tbody>
              </table>
            </div>
            <div class="lx-foot">
              <span id="or-foot">—</span>
              <a onclick="ozExportCSV()">Download what's shown as CSV</a>
            </div>
          </div>

          <div id="or-email" style="display:none">
            <div class="lx-stats" id="or-estats" style="grid-template-columns:repeat(5,1fr);margin-bottom:16px"></div>
            <div class="lx-tablewrap">
              <table class="lx-tbl">
                <thead><tr>
                  <th>Contact</th><th>Firm</th><th>Email</th><th>State</th>
                  <th>Touches</th><th>Last sent</th><th>Status</th><th style="min-width:200px">Log a touch</th>
                </tr></thead>
                <tbody id="or-email-body"></tbody>
              </table>
            </div>
            <div class="lx-foot"><span id="or-efoot">—</span></div>
          </div>
        </div>

      </div>
    </div><!-- /page-outreach -->

    <!-- paste-a-list importer (patch 286) -->
    <div class="oz-shade" id="oz-import">
      <div class="oz-modal">
        <div class="oz-mhd">
          <div>
            <h3>Paste a list of firms</h3>
            <p>Paste straight from a spreadsheet, a CSV, or a plain list — one firm per line. Emails, phone numbers, states and websites are picked out on their own. Check the preview, fix anything that landed in the wrong column, then import.</p>
          </div>
          <button class="lx-x" onclick="ozCloseImport()">×</button>
        </div>
        <div class="oz-mbody">
          <textarea class="oz-ta" id="oz-paste" placeholder="Morgan &amp; Associates, John Morgan, john@morganlaw.com, PA&#10;Keller Injury Law&#9;keller@kellerinjury.com&#9;215-555-0142&#9;PA&#10;Shapiro Law Group — info@shapirolawgroup.com — Philadelphia PA"></textarea>
          <div class="oz-mrow">
            <button class="lx-btn" onclick="ozParsePaste()">Read the list</button>
            <label class="oz-note">Vertical <select class="lx-winsel" id="oz-vert"><option value="MVA">MVA</option><option value="SSDI">SSDI</option><option value="Mass Tort">Mass Tort</option><option value="">None</option></select></label>
            <label class="oz-note">Role <select class="lx-winsel" id="oz-role"><option value="buyer">Buyer (law firm)</option><option value="seller">Seller (publisher)</option><option value="both">Both</option></select></label>
            <label class="oz-note">Source <select class="lx-winsel" id="oz-src"><option value="List">Pasted list</option><option value="LinkedIn">LinkedIn</option><option value="Referral">Referral</option><option value="Email">Email</option><option value="Other">Other</option></select></label>
            <span class="oz-note" id="oz-parsed"></span>
          </div>
          <div class="oz-prev" id="oz-prevwrap" style="display:none">
            <table><thead><tr><th style="width:34px"></th><th>Firm</th><th>Contact name</th><th>Email</th><th>Phone</th><th>State</th><th style="width:92px">Status</th></tr></thead><tbody id="oz-prevbody"></tbody></table>
          </div>
          <div class="oz-mfoot">
            <span class="oz-note" id="oz-sum">Nothing read yet.</span>
            <span style="display:flex;gap:10px">
              <button class="lx-btn quiet" onclick="ozCloseImport()">Cancel</button>
              <button class="lx-btn" id="oz-go" onclick="ozImport()" disabled>Import</button>
            </span>
          </div>
        </div>
      </div>
    </div>
'''

m = re.search(r'[ \t]*<!-- ═══ OUTREACH PAGE ═══ -->.*?</div><!-- /page-outreach -->\n',
              src, re.S)
if not m:
    sys.exit("could not find the #page-outreach block - aborting, index.html untouched")
src = src[:m.start()] + HTML + src[m.end():]

# ──────────────────────────────────────────────────────────────────────────────
# 3. JS - appended at the end of the dashboard script block
# ──────────────────────────────────────────────────────────────────────────────
JS = r'''
// ══════════════════════════════════════════════════════════════════════════
//  OUTREACH v2  (patch 286)
//  Redefines the render layer only. Contact data, orSave/orFetch/orPush and
//  the edit modal are the originals; the last function declaration wins.
// ══════════════════════════════════════════════════════════════════════════
var ozSortKey='followup', ozSortDir='asc', ozStatFilter='';
var OZ_STATES={AL:1,AK:1,AZ:1,AR:1,CA:1,CO:1,CT:1,DE:1,FL:1,GA:1,HI:1,ID:1,IL:1,IN:1,IA:1,KS:1,KY:1,LA:1,ME:1,MD:1,MA:1,MI:1,MN:1,MS:1,MO:1,MT:1,NE:1,NV:1,NH:1,NJ:1,NM:1,NY:1,NC:1,ND:1,OH:1,OK:1,OR:1,PA:1,RI:1,SC:1,SD:1,TN:1,TX:1,UT:1,VT:1,VA:1,WA:1,WV:1,WI:1,WY:1,DC:1};
var OZ_STATE_NAMES={'alabama':'AL','alaska':'AK','arizona':'AZ','arkansas':'AR','california':'CA','colorado':'CO','connecticut':'CT','delaware':'DE','florida':'FL','georgia':'GA','hawaii':'HI','idaho':'ID','illinois':'IL','indiana':'IN','iowa':'IA','kansas':'KS','kentucky':'KY','louisiana':'LA','maine':'ME','maryland':'MD','massachusetts':'MA','michigan':'MI','minnesota':'MN','mississippi':'MS','missouri':'MO','montana':'MT','nebraska':'NE','nevada':'NV','new hampshire':'NH','new jersey':'NJ','new mexico':'NM','new york':'NY','north carolina':'NC','north dakota':'ND','ohio':'OH','oklahoma':'OK','oregon':'OR','pennsylvania':'PA','rhode island':'RI','south carolina':'SC','south dakota':'SD','tennessee':'TN','texas':'TX','utah':'UT','vermont':'VT','virginia':'VA','washington':'WA','west virginia':'WV','wisconsin':'WI','wyoming':'WY'};

function ozEsc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function ozToday(){return new Date().toISOString().split('T')[0];}
function ozDays(d){if(!d)return null;var t=Date.parse(d);if(isNaN(t))return null;return Math.floor((new Date(ozToday())-new Date(d))/86400000);}
function ozEmail(c){var v=String(c.contact||'').trim();return v.indexOf('@')>0?v:'';}
function ozPhone(c){var v=String(c.contact||'').trim();if(v.indexOf('@')>0)return '';var d=v.replace(/\D/g,'');return d.length>=10?v:'';}
function ozOverdue(c){return !!c.followup && c.followup <= ozToday();}
function ozStale(c){var d=ozDays(c.lastContact);return c.stage!=='cold' && d!==null && d>=7;}

// ── summary ───────────────────────────────────────────────────────────────
function renderOrStats(){
  var t=orData.length, by={};
  STAGES.forEach(function(s){by[s]=orData.filter(function(c){return c.stage===s;}).length;});
  var worked=t-by.cold, resp=by.responded+by.intalks+by.ready;
  var mail=orData.filter(function(c){return ozEmail(c);}).length;
  var due=orData.filter(ozOverdue).length;
  var el=document.getElementById('or-stats'); if(!el)return;
  function card(key,label,n,sub,delta){
    return '<div class="lx-stat'+(ozStatFilter===key?' on':'')+'" onclick="ozStat(\''+key+'\')" title="Click to filter the pipeline">'+
      '<span class="pin">filtering</span><div style="font-size:14px;color:var(--lx-ink-2)">'+label+'</div>'+
      '<div class="n">'+n+'</div><div class="sub">'+sub+'</div>'+(delta?'<div class="delta">'+delta+'</div>':'')+'</div>';
  }
  el.innerHTML =
    card('all','In the pipeline',t,'<b>'+mail+'</b> have an email on file','') +
    card('cold','Not yet touched',by.cold, by.cold?'waiting on a first message':'everyone has been contacted','') +
    card('resp','Replied or better',resp,(worked?Math.round(100*resp/worked):0)+'% of everyone contacted', by.ready?by.ready+' ready to deal':'') +
    card('due','Follow-ups due',due, due?'overdue or due today':'nothing overdue','');
  var note=document.getElementById('or-sum-note');
  if(note) note.innerHTML='<i></i><span>'+worked+' of '+t+' contacted · '+by.intalks+' in talks</span>';
}
function ozStat(k){ if(k==='all')k=''; ozStatFilter = (ozStatFilter===k?'':k); renderOutreach(); }
// a firm-only contact carries the firm as its name too; don't print it twice
function ozSub(c){
  var bits=[];
  if(c.company && String(c.company).trim()!==String(c.name).trim()) bits.push(c.company);
  if(c.state) bits.push(c.state);
  return bits.join(' · ');
}

// ── filtering ─────────────────────────────────────────────────────────────
function getFiltered(){
  function val(id){var e=document.getElementById(id);return e?(e.value||''):'';}
  var q=val('or-search').toLowerCase(), role=val('or-role'), stage=val('or-stage'), vert=val('or-vert');
  return orData.filter(function(c){
    if(role&&c.role!==role)return false;
    if(stage&&c.stage!==stage)return false;
    if(vert){var vv=String(c.vertical||'').toUpperCase();
      if(vert==='OTHER'){ if(vv.indexOf('MVA')>-1||vv.indexOf('SSDI')>-1)return false; }
      else if(vv.indexOf(vert)<0)return false;}
    if(ozStatFilter==='cold'&&c.stage!=='cold')return false;
    if(ozStatFilter==='resp'&&['responded','intalks','ready'].indexOf(c.stage)<0)return false;
    if(ozStatFilter==='due'&&!ozOverdue(c))return false;
    if(q){
      var hay=[c.name,c.company,c.contact,c.state,c.vertical,c.offer,c.notes].join(' ').toLowerCase();
      if(hay.indexOf(q)<0)return false;
    }
    return true;
  });
}
function ozSort(k){ if(ozSortKey===k){ozSortDir=ozSortDir==='asc'?'desc':'asc';}else{ozSortKey=k;ozSortDir='asc';} renderOutreach(); }
function ozSorted(list){
  var k=ozSortKey,d=ozSortDir==='asc'?1:-1;
  return list.slice().sort(function(a,b){
    var x=a[k],y=b[k];
    if(k==='stage'){x=STAGES.indexOf(a.stage);y=STAGES.indexOf(b.stage);}
    if(x==null||x==='')return 1; if(y==null||y==='')return -1;
    if(typeof x==='string')return d*x.localeCompare(String(y));
    return d*(x-y);
  });
}

// ── work queue ────────────────────────────────────────────────────────────
function renderOrToday(){
  var box=document.getElementById('or-today'); if(!box)return;
  var today=ozToday(), items=[];
  orData.forEach(function(c){
    if(c.emailStatus==='replied'){ items.push({c:c,rank:0,when:'Replied',sub:'waiting on you',cls:'now'}); return; }
    if(c.followup){
      var dd=Math.round((new Date(c.followup)-new Date(today))/86400000);
      if(dd<0) items.push({c:c,rank:1+dd/1000,when:(-dd)+'d late',sub:'due '+c.followup,cls:'late'});
      else if(dd===0) items.push({c:c,rank:2,when:'Today',sub:'follow-up due',cls:'now'});
      return;
    }
    if(ozStale(c)){ var d=ozDays(c.lastContact); items.push({c:c,rank:3+(100-Math.min(d,99))/1000,when:d+'d quiet',sub:c.lastContact,cls:''}); }
  });
  items.sort(function(a,b){return a.rank-b.rank;});
  var sub=document.getElementById('or-today-sub');
  if(sub) sub.textContent = items.length ? items.length+(items.length===1?' contact':' contacts')+' waiting' : '';
  if(!items.length){ box.innerHTML='<div class="oz-calm">Nothing is overdue. <b>The list is clear.</b></div>'; return; }
  box.innerHTML='<ul class="oz-queue">'+items.slice(0,25).map(function(it){
    var c=it.c, em=ozEmail(c);
    return '<li>'+
      '<span class="oz-when '+it.cls+'">'+ozEsc(it.when)+'<small>'+ozEsc(it.sub)+'</small></span>'+
      '<span class="oz-who" onclick="openContactModal('+c.id+')"><b>'+ozEsc(c.name)+'</b>'+
        '<span class="sub">'+ozEsc([ozSub(c),em].filter(Boolean).join(' · ')||'no firm or email on file')+'</span></span>'+
      '<span class="oz-do">'+
        (em?'<a class="lx-btn quiet sm" href="mailto:'+ozEsc(em)+'" onclick="event.stopPropagation()">Email</a>':'')+
        '<button class="lx-btn quiet sm" onclick="event.stopPropagation();ozTouch('+c.id+')">Logged a touch</button>'+
        '<button class="lx-btn quiet sm" onclick="event.stopPropagation();ozSnooze('+c.id+',7)">Snooze 7d</button>'+
      '</span></li>';
  }).join('')+'</ul>';
}
function ozTouch(id){
  var c=orData.find(function(x){return x.id===id;}); if(!c)return;
  c.lastContact=ozToday();
  c.followup=new Date(Date.now()+4*86400000).toISOString().split('T')[0];
  if(c.stage==='cold')c.stage='contacted';
  orSave(); renderOutreach(); if(typeof showToast==='function')showToast(c.name+' — touch logged, follow-up in 4 days');
}
function ozSnooze(id,days){
  var c=orData.find(function(x){return x.id===id;}); if(!c)return;
  c.followup=new Date(Date.now()+days*86400000).toISOString().split('T')[0];
  orSave(); renderOutreach(); if(typeof showToast==='function')showToast(c.name+' — snoozed '+days+' days');
}

// ── views ─────────────────────────────────────────────────────────────────
function setOrView(v){
  orView=v;
  [['board','or-board'],['list','or-list'],['email','or-email']].forEach(function(p){
    var e=document.getElementById(p[1]); if(e)e.style.display=(orView===p[0]?'':'none');
    var b=document.getElementById('vbtn-'+p[0]); if(b)b.setAttribute('aria-pressed',orView===p[0]?'true':'false');
  });
  renderOutreach();
}
function renderOutreach(){
  if(typeof orData==='undefined')return;
  renderOrStats(); renderOrToday();
  var list=getFiltered();
  var cnt=document.getElementById('or-count');
  if(cnt)cnt.textContent=list.length+' of '+orData.length+' shown';
  var live=document.getElementById('or-live'), lt=document.getElementById('or-live-txt');
  if(live&&lt){ live.className='lx-live'+(orLoaded?' on':''); lt.textContent=orLoaded?'Synced':'Local copy'; }
  if(orView==='board')renderBoard(list);
  else if(orView==='email')renderEmailTab(list);
  else renderList(list);
}

function renderBoard(contacts){
  var board=document.getElementById('or-board'); if(!board)return;
  board.innerHTML=STAGES.map(function(s){
    return '<div class="oz-col" data-stage="'+s+'"><div class="oz-colhd"><h4>'+STAGE_LABELS[s]+'</h4><span class="n" id="ozn-'+s+'">0</span></div><div class="oz-colbody" id="ozb-'+s+'"></div></div>';
  }).join('');
  STAGES.forEach(function(stage){
    var col=board.querySelector('.oz-col[data-stage="'+stage+'"]');
    var body=document.getElementById('ozb-'+stage);
    var sc=contacts.filter(function(c){return c.stage===stage;});
    var n=document.getElementById('ozn-'+stage); if(n)n.textContent=sc.length;
    col.ondragover=function(e){e.preventDefault();col.classList.add('drop');};
    col.ondragleave=function(e){if(!col.contains(e.relatedTarget))col.classList.remove('drop');};
    col.ondrop=function(e){
      e.preventDefault(); col.classList.remove('drop');
      if(dragId===null)return;
      var c=orData.find(function(x){return x.id===dragId;});
      if(c&&c.stage!==stage){ c.stage=stage; c.lastContact=c.lastContact||ozToday(); orSave(); renderOutreach();
        if(typeof showToast==='function')showToast(c.name+' → '+STAGE_LABELS[stage]); }
      dragId=null;
    };
    if(!sc.length){ body.innerHTML='<div class="oz-empty">Drop here</div>'; return; }
    body.innerHTML='';
    sc.forEach(function(c){
      var em=ozEmail(c), late=ozOverdue(c), d=ozDays(c.lastContact);
      var card=document.createElement('div');
      card.className='oz-card'; card.setAttribute('draggable','true');
      card.innerHTML='<button class="x" title="Delete" onclick="event.stopPropagation();deleteContact('+c.id+')">×</button>'+
        '<div class="nm">'+ozEsc(c.name)+'</div>'+
        (ozSub(c)?'<div class="co">'+ozEsc(ozSub(c))+'</div>':'')+
        (em?'<div class="em">'+ozEsc(em)+'</div>':'')+
        '<div class="ft"><span'+(late?' class="late"':'')+'>'+(c.followup?(late?'Due '+c.followup:'Follow-up '+c.followup):(d!==null?d+'d since touch':'No contact yet'))+'</span>'+
        (c.potential>0?'<span>~$'+Number(c.potential).toLocaleString()+'</span>':'')+'</div>';
      card.ondragstart=function(e){dragId=c.id;card.classList.add('dragging');e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text/plain',String(c.id));};
      card.ondragend=function(){card.classList.remove('dragging');dragId=null;
        Array.prototype.forEach.call(document.querySelectorAll('.oz-col'),function(x){x.classList.remove('drop');});};
      card.addEventListener('click',function(e){ if(e.target.className!=='x')openContactModal(c.id); });
      body.appendChild(card);
    });
  });
}

function renderList(contacts){
  var tb=document.getElementById('or-list-body'); if(!tb)return;
  var rows=ozSorted(contacts);
  Array.prototype.forEach.call(document.querySelectorAll('#or-list th.sortable'),function(th){
    th.classList.remove('sorted-asc','sorted-desc');
    if(th.getAttribute('data-key')===ozSortKey)th.classList.add(ozSortDir==='asc'?'sorted-asc':'sorted-desc');
  });
  var foot=document.getElementById('or-foot');
  if(foot)foot.textContent=rows.length+' contact'+(rows.length===1?'':'s')+' shown';
  if(!rows.length){ tb.innerHTML='<tr><td colspan="9" class="lx-empty">Nothing matches those filters. <a onclick="ozClearFilters()">Clear them</a> or <a onclick="ozOpenImport()">paste a list of firms</a>.</td></tr>'; return; }
  tb.innerHTML='';
  rows.forEach(function(c){
    var em=ozEmail(c), ph=ozPhone(c), late=ozOverdue(c), d=ozDays(c.lastContact);
    var tr=document.createElement('tr');
    tr.innerHTML=
      '<td><span class="big">'+ozEsc(c.name)+'</span>'+(c.offer?'<span class="sm">'+ozEsc(String(c.offer).slice(0,60))+'</span>':'')+'</td>'+
      '<td>'+(c.company?ozEsc(c.company):'<span style="color:var(--lx-ink-3)">—</span>')+'</td>'+
      '<td>'+(em?'<a href="mailto:'+ozEsc(em)+'" onclick="event.stopPropagation()" style="color:var(--lx-green-2)">'+ozEsc(em)+'</a>':(ph?ozEsc(ph):'<span style="color:var(--lx-ink-3)">—</span>'))+'</td>'+
      '<td>'+(c.state?ozEsc(c.state):'<span style="color:var(--lx-ink-3)">—</span>')+'</td>'+
      '<td>'+(c.vertical?'<span class="lx-pill camp">'+ozEsc(c.vertical)+'</span>':'<span style="color:var(--lx-ink-3)">—</span>')+'</td>'+
      '<td><span class="oz-pill '+c.stage+'">'+STAGE_LABELS[c.stage]+'</span></td>'+
      '<td class="num">'+(c.lastContact?ozEsc(c.lastContact)+'<span class="sm">'+d+'d ago</span>':'<span style="color:var(--lx-ink-3)">never</span>')+'</td>'+
      '<td class="num"'+(late?' style="color:var(--lx-red);font-weight:600"':'')+'>'+(c.followup?ozEsc(c.followup):'<span style="color:var(--lx-ink-3)">—</span>')+'</td>'+
      '<td><button class="lx-btn quiet sm" onclick="event.stopPropagation();ozTouch('+c.id+')">Touch</button></td>';
    tr.addEventListener('click',function(e){ if(e.target.tagName!=='BUTTON'&&e.target.tagName!=='A')openContactModal(c.id); });
    tb.appendChild(tr);
  });
}

function renderEmailTab(contacts){
  var all=orData.filter(function(c){return ozEmail(c);});
  var sent=all.filter(function(c){return (c.emailsSent||0)>0;});
  var rep=all.filter(function(c){return c.emailStatus==='replied'||c.emailStatus==='meeting';});
  var meet=all.filter(function(c){return c.emailStatus==='meeting';});
  var st=document.getElementById('or-estats');
  if(st) st.innerHTML=[
    ['Mailable',all.length,'contacts with an email'],
    ['Emailed',sent.length,(all.length?Math.round(100*sent.length/all.length):0)+'% of mailable'],
    ['Replied',rep.length,(sent.length?Math.round(100*rep.length/sent.length):0)+'% reply rate'],
    ['Meetings',meet.length,(sent.length?Math.round(100*meet.length/sent.length):0)+'% of emailed'],
    ['No email yet',orData.length-all.length,'need an address before they can be worked']
  ].map(function(s){return '<div class="lx-stat"><div style="font-size:14px;color:var(--lx-ink-2)">'+s[0]+'</div><div class="n">'+s[1]+'</div><div class="sub">'+s[2]+'</div></div>';}).join('');
  var tb=document.getElementById('or-email-body'); if(!tb)return;
  var rows=ozSorted((contacts||all).filter(function(c){return ozEmail(c);}));
  var foot=document.getElementById('or-efoot');
  if(foot)foot.textContent=rows.length+' mailable contact'+(rows.length===1?'':'s')+' shown';
  if(!rows.length){ tb.innerHTML='<tr><td colspan="8" class="lx-empty">No contacts with an email address match. <a onclick="ozOpenImport()">Paste a list of firms</a> to add some.</td></tr>'; return; }
  tb.innerHTML='';
  rows.forEach(function(c){
    var em=ozEmail(c), n=c.emailsSent||0, s=c.emailStatus||'';
    var chip = s==='meeting'?'<span class="oz-pill meet">Meeting set</span>'
             : s==='replied'?'<span class="oz-pill rep">Replied</span>'
             : n>0?'<span class="oz-pill seq">In sequence · '+n+'</span>'
             : '<span class="oz-pill cold">Not started</span>';
    var tr=document.createElement('tr');
    tr.innerHTML='<td><span class="big">'+ozEsc(c.name)+'</span></td>'+
      '<td>'+ozEsc(c.company||'—')+'</td>'+
      '<td><a href="mailto:'+ozEsc(em)+'" onclick="event.stopPropagation()" style="color:var(--lx-green-2)">'+ozEsc(em)+'</a></td>'+
      '<td>'+ozEsc(c.state||'—')+'</td>'+
      '<td class="num">'+n+'</td>'+
      '<td class="num">'+(c.lastEmailAt||'—')+'</td>'+
      '<td>'+chip+'</td>'+
      '<td><button class="lx-btn quiet sm" onclick="event.stopPropagation();orMarkEmail('+c.id+',\'sent\')">Sent</button> '+
          '<button class="lx-btn quiet sm" onclick="event.stopPropagation();orMarkEmail('+c.id+',\'replied\')">Replied</button> '+
          '<button class="lx-btn quiet sm" onclick="event.stopPropagation();orMarkEmail('+c.id+',\'meeting\')">Meeting</button></td>';
    tr.addEventListener('click',function(e){ if(e.target.tagName!=='BUTTON'&&e.target.tagName!=='A')openContactModal(c.id); });
    tb.appendChild(tr);
  });
}

function ozClearFilters(){
  ['or-search','or-role','or-vert','or-stage'].forEach(function(id){var e=document.getElementById(id);if(e)e.value='';});
  ozStatFilter=''; renderOutreach();
}
function ozExportCSV(){
  var rows=ozSorted(getFiltered());
  var head=['Name','Firm','Email','Phone','State','Vertical','Role','Stage','Source','Last contact','Follow-up','Emails sent','Email status','Potential','Offer','Notes'];
  function q(v){return '"'+String(v==null?'':v).replace(/"/g,'""')+'"';}
  var csv=[head.join(',')].concat(rows.map(function(c){
    return [c.name,c.company,ozEmail(c),ozPhone(c),c.state,c.vertical,c.role,STAGE_LABELS[c.stage]||c.stage,c.source,c.lastContact,c.followup,c.emailsSent||0,c.emailStatus||'',c.potential||0,c.offer,c.notes].map(q).join(',');
  })).join('\n');
  var a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
  a.download='krw-outreach-'+ozToday()+'.csv'; a.click();
}

// ── paste-a-list importer ─────────────────────────────────────────────────
var ozRows=[];
function ozOpenImport(){ document.getElementById('oz-import').classList.add('open'); setTimeout(function(){var t=document.getElementById('oz-paste');if(t)t.focus();},50); }
function ozCloseImport(){ document.getElementById('oz-import').classList.remove('open'); }
function ozFindState(parts,whole){
  for(var i=0;i<parts.length;i++){
    var p=parts[i].trim();
    if(p.length===2&&OZ_STATES[p.toUpperCase()])return p.toUpperCase();
    if(OZ_STATE_NAMES[p.toLowerCase()])return OZ_STATE_NAMES[p.toLowerCase()];
  }
  var m=whole.match(/\b([A-Z]{2})\b(?=\s*\d{5}|\s*$|\s*[,·|])/g);
  if(m){for(var j=0;j<m.length;j++){var s=m[j].trim().toUpperCase();if(OZ_STATES[s])return s;}}
  for(var nm in OZ_STATE_NAMES){ if(whole.toLowerCase().indexOf(nm)>-1)return OZ_STATE_NAMES[nm]; }
  return '';
}
function ozLooksLikePerson(s){
  s=s.trim();
  if(!s||s.length>44)return false;
  if(/\b(law|legal|llp|llc|p\.?c\.?|pllc|firm|group|associates|injury|attorney|partners|office)\b/i.test(s))return false;
  var w=s.split(/\s+/);
  if(w.length<2||w.length>4)return false;
  if(!/^[A-Z][a-z'`-]+$/.test(w[0]))return false;
  // "Philadelphia PA" / "Salt Lake City Utah" is a place, not a person
  var last=w[w.length-1];
  if(last.length===2&&OZ_STATES[last.toUpperCase()])return false;
  for(var i=0;i<w.length;i++){ if(OZ_STATE_NAMES[w[i].toLowerCase()])return false; }
  return true;
}
var OZ_FIRMWORD=/\b(law|legal|llp|llc|p\.?c\.?|pllc|firm|group|associates|injury|attorney|attorneys|partners|office|offices|&)\b/i;
function ozPickFirm(parts){
  // a part that reads like a firm wins; otherwise the first one, since lists
  // lead with the firm and a city would otherwise win on length alone
  for(var i=0;i<parts.length;i++){ if(OZ_FIRMWORD.test(parts[i]))return parts[i]; }
  return parts[0]||'';
}
function ozStripState(s,st){
  s=String(s||'').trim();
  if(st) s=s.replace(new RegExp('[\\s,·|-]*\\b'+st+'\\b\\s*$','i'),'').trim();
  for(var nm in OZ_STATE_NAMES){
    s=s.replace(new RegExp('[\\s,·|-]*\\b'+nm+'\\b\\s*$','i'),'').trim();
  }
  return s.replace(/^[\s,;|·—–-]+|[\s,;|·—–-]+$/g,'').trim();
}
function ozParsePaste(){
  var raw=(document.getElementById('oz-paste').value||'').trim();
  ozRows=[];
  if(!raw){ document.getElementById('oz-parsed').textContent='Paste something first.'; return; }
  var lines=raw.split(/\r?\n/).map(function(l){return l.trim();}).filter(function(l){return l;});
  // drop a header row
  if(lines.length>1 && /firm|company|name|email/i.test(lines[0]) && !/@/.test(lines[0])) lines.shift();
  var seenEmail={}, seenFirm={};
  orData.forEach(function(c){ var e=ozEmail(c); if(e)seenEmail[e.toLowerCase()]=1; if(c.company)seenFirm[String(c.company).toLowerCase().replace(/[^a-z0-9]/g,'')]=1; });
  lines.forEach(function(line){
    var email=(line.match(/[\w.+-]+@[\w-]+\.[\w.-]+/)||[''])[0];
    var rest=line.replace(email,' ');
    var phone=(rest.match(/(\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}/)||[''])[0];
    rest=rest.replace(phone,' ');
    var site=(rest.match(/(https?:\/\/)?(www\.)?[\w-]+\.(com|net|org|law|co|us)\b/i)||[''])[0];
    rest=rest.replace(site,' ');
    var parts=rest.split(/\t|\s*[,;|·—–]\s*|\s{2,}/).map(function(p){return p.trim();}).filter(function(p){return p&&!/^\d+$/.test(p);});
    var state=ozFindState(parts,line);
    parts=parts.filter(function(p){
      var u=p.trim().toUpperCase();
      if(u===state)return false;
      if(p.length===2&&OZ_STATES[u])return false;
      if(OZ_STATE_NAMES[p.toLowerCase()])return false;
      return true;
    });
    var person='', firm='';
    for(var i=0;i<parts.length;i++){ if(!person&&ozLooksLikePerson(parts[i])&&parts.length>1){person=parts[i];parts.splice(i,1);break;} }
    firm=ozStripState(ozPickFirm(parts),state);
    person=ozStripState(person,state);
    if(!firm&&!person&&!email)return;
    if(!firm&&site)firm=site.replace(/^https?:\/\//,'').replace(/^www\./,'');
    var key=String(firm).toLowerCase().replace(/[^a-z0-9]/g,'');
    var dup = (email&&seenEmail[email.toLowerCase()]) || (key&&seenFirm[key]);
    ozRows.push({firm:firm,person:person,email:email,phone:phone,state:state,site:site,dup:!!dup,skip:!!dup});
    if(email)seenEmail[email.toLowerCase()]=1;
    if(key)seenFirm[key]=1;
  });
  ozRenderPreview();
}
function ozRenderPreview(){
  var tb=document.getElementById('oz-prevbody'), wrap=document.getElementById('oz-prevwrap');
  if(!tb)return;
  wrap.style.display=ozRows.length?'':'none';
  tb.innerHTML=ozRows.map(function(r,i){
    return '<tr class="'+(r.skip?'skip':(r.dup?'dup':''))+'">'+
      '<td><input type="checkbox" '+(r.skip?'':'checked')+' onchange="ozRows['+i+'].skip=!this.checked;ozRenderPreview()"></td>'+
      '<td><input value="'+ozEsc(r.firm)+'" oninput="ozRows['+i+'].firm=this.value"></td>'+
      '<td><input value="'+ozEsc(r.person)+'" oninput="ozRows['+i+'].person=this.value" placeholder="—"></td>'+
      '<td><input value="'+ozEsc(r.email)+'" oninput="ozRows['+i+'].email=this.value" placeholder="—"></td>'+
      '<td><input value="'+ozEsc(r.phone)+'" oninput="ozRows['+i+'].phone=this.value" placeholder="—"></td>'+
      '<td><input value="'+ozEsc(r.state)+'" oninput="ozRows['+i+'].state=this.value" placeholder="—" style="width:46px"></td>'+
      '<td style="font-size:12.5px;color:var(--lx-ink-3)">'+(r.dup?'already here':'new')+'</td></tr>';
  }).join('');
  var keep=ozRows.filter(function(r){return !r.skip;}).length;
  var dups=ozRows.filter(function(r){return r.dup;}).length;
  var noEmail=ozRows.filter(function(r){return !r.skip&&!r.email;}).length;
  document.getElementById('oz-parsed').textContent=ozRows.length+' line'+(ozRows.length===1?'':'s')+' read';
  var sum=document.getElementById('oz-sum');
  sum.innerHTML='<b>'+keep+'</b> will be imported'+
    (dups?' · <span>'+dups+' already in the board, unticked</span>':'')+
    (noEmail?' · <span class="oz-warn">'+noEmail+' with no email — they can be worked by phone but not emailed</span>':'');
  document.getElementById('oz-go').disabled = keep===0;
}
function ozImport(){
  var vert=document.getElementById('oz-vert').value;
  var role=document.getElementById('oz-role').value;
  var srcv=document.getElementById('oz-src').value;
  var add=ozRows.filter(function(r){return !r.skip && (r.firm||r.person||r.email);});
  if(!add.length)return;
  var next=orNextId();
  add.forEach(function(r){
    orData.push({
      id:next++,
      name:(r.person||r.firm||r.email),
      company:r.firm||'',
      role:role, vertical:vert, stage:'cold', source:srcv,
      state:(r.state||'').toUpperCase(),
      lastContact:'', followup:'',
      contact:r.email||r.phone||'',
      phone:r.phone||'', website:r.site||'',
      potential:0, offer:'', notes:'Imported '+ozToday(),
      emailsSent:0, emailStatus:''
    });
  });
  orSave(); ozCloseImport();
  document.getElementById('oz-paste').value=''; ozRows=[]; ozRenderPreview();
  ozStatFilter=''; ozClearFilters();
  if(typeof showToast==='function')showToast(add.length+' contact'+(add.length===1?'':'s')+' imported');
}
document.addEventListener('click',function(e){ var m=document.getElementById('oz-import'); if(m&&e.target===m)ozCloseImport(); });
document.addEventListener('keydown',function(e){ if(e.key==='Escape'){var m=document.getElementById('oz-import'); if(m&&m.classList.contains('open'))ozCloseImport();} });
// ── end patch 286 ─────────────────────────────────────────────────────────
'''

idx = src.find("</script>")
if idx < 0:
    sys.exit("no </script> found - aborting")
src = src[:idx] + JS + "\n" + src[idx:]

shutil.copy2(TARGET, TARGET + ".pre-286.bak")
open(TARGET, "w", encoding="utf-8").write(src)
print("patch 286 applied. backup: index.html.pre-286.bak")
print("open index.html, click Outreach, then: git add -A && git commit -m 'patch 286' && git push")
