#!/usr/bin/env python3
"""
patch-344.py  --  case counts, a range picker, and click a buyer to see the leads

Needs patch 343 on the backend.

  1. CASES column in the By buyer table, so the owed figure comes with the
     number of cases behind it.

  2. RANGE PICKER (1 week / 2 weeks / Month / All time) in the Leads page's
     own .lx-seg style. Defaults to All time, matching the backend, so no owed
     money is ever hidden by a filter nobody set.

  3. CLICK A BUYER to expand every case making up what they owe: lead name,
     phone, state, publisher, what the buyer pays, what the publisher is paid,
     the margin on that case, its age, and whether it is invoiced or overdue.
     Rows where the publisher payout is unknown show the margin as a dash
     rather than as the full amount, so an unknown cost never reads as profit.

     The expanded row is built from the data object, same as the rest.

Backup: index.html.pre-344.bak    Safe to re-run: refuses twice.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def find_root():
    for c in (HERE, os.path.dirname(HERE), os.getcwd(), os.path.dirname(os.getcwd())):
        if os.path.isfile(os.path.join(c, "portal", "index.html")):
            return os.path.join(c, "portal")
        if os.path.isfile(os.path.join(c, "index.html")) and os.path.basename(c) == "portal":
            return c
    return None


ROOT = find_root() or sys.exit("run from ~/krw (needs portal/index.html)")
FILE = os.path.join(ROOT, "index.html")
src = open(FILE, encoding="utf-8").read()

if "patch 344" in src:
    sys.exit("patch 344 already applied - nothing to do")
if "patch 339" not in src:
    sys.exit("patch 339 is not applied - run patch-339.py first")

# ── 1. Range picker in the section header ────────────────────────────────
OLD_HEAD = """          <div class="lx-sechead">
            <h3>MVA money</h3>
            <button class="lx-btn quiet sm" onclick="fetchFundingSummary()">Refresh</button>
          </div>"""
NEW_HEAD = """          <div class="lx-sechead">
            <h3>MVA money</h3>
            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
              <div class="lx-seg" id="fs-range-seg">
                <button data-r="week" onclick="fsSetRange('week')">1 week</button>
                <button data-r="biweek" onclick="fsSetRange('biweek')">2 weeks</button>
                <button data-r="month" onclick="fsSetRange('month')">Month</button>
                <button data-r="all" aria-pressed="true" onclick="fsSetRange('all')">All time</button>
              </div>
              <button class="lx-btn quiet sm" onclick="fetchFundingSummary()">Refresh</button>
            </div>
          </div>"""
if src.count(OLD_HEAD) != 1:
    sys.exit("section header found %d times, expected 1 - aborting" % src.count(OLD_HEAD))
src = src.replace(OLD_HEAD, NEW_HEAD, 1)

# ── 2. Range state + fetch with the range ────────────────────────────────
OLD_STATE = "      var fsData = null, fsPnlMode = 'weekly';"
NEW_STATE = ("      var fsData = null, fsPnlMode = 'weekly', fsRange = 'all';\n"
             "      var fsOpenBuyers = {};   /* which buyer rows are expanded */")
if src.count(OLD_STATE) != 1:
    sys.exit("state line found %d times, expected 1 - aborting" % src.count(OLD_STATE))
src = src.replace(OLD_STATE, NEW_STATE, 1)

OLD_FETCH = "          var res = await fetch(REV_API_URL+'/funding-summary', { headers:{'x-api-key':REV_API_KEY} });"
NEW_FETCH = "          var res = await fetch(REV_API_URL+'/funding-summary?range='+encodeURIComponent(fsRange), { headers:{'x-api-key':REV_API_KEY} });"
if src.count(OLD_FETCH) != 1:
    sys.exit("fetch line found %d times, expected 1 - aborting" % src.count(OLD_FETCH))
src = src.replace(OLD_FETCH, NEW_FETCH, 1)

# ── 3. Replace the buyer table renderer with counts + expandable detail ──
OLD_START = "      function fsRenderBuyers(buyers, readyBuyers){"
OLD_END = "      function fsRenderInvoices(list){"
if src.count(OLD_START) != 1 or src.count(OLD_END) != 1:
    sys.exit("buyer renderer bounds not unique - aborting, nothing changed")
a, b = src.index(OLD_START), src.index(OLD_END)
if b <= a:
    sys.exit("renderer bounds out of order - aborting")

NEW_RENDER = r'''      /* patch 344: range picker, case counts, and per-buyer drill-down. */
      function fsSetRange(r){
        fsRange = r;
        var seg = document.getElementById('fs-range-seg');
        Array.prototype.forEach.call(seg.querySelectorAll('button'), function(b){
          b.setAttribute('aria-pressed', b.getAttribute('data-r')===r ? 'true' : 'false');
        });
        fetchFundingSummary();
      }

      function fsToggleBuyer(buyer){
        fsOpenBuyers[buyer] = !fsOpenBuyers[buyer];
        if(fsData) fsRenderBuyers(fsData.by_buyer||[], (fsData.ready_to_invoice||{}).by_buyer||[]);
      }

      function fsDetailRows(b){
        var d = b.detail || [];
        if(!d.length) return '<div class="fs-none">No case detail for this buyer.</div>';
        var rows = '';
        d.forEach(function(c){
          var status = c.overdue ? '<span class="fs-tag late">'+c.days_overdue+'d late</span>'
                     : c.invoiced ? '<span class="fs-tag ok">invoiced</span>'
                     : '<span class="fs-tag hold">not invoiced</span>';
          rows += '<tr>'+
            '<td data-l="Lead">'+fsEsc(c.name||'—')+(c.source==='manual'?' <span class="fs-tag hold">added</span>':'')+'</td>'+
            '<td data-l="Phone">'+fsEsc(c.cid||'—')+'</td>'+
            '<td data-l="State">'+fsEsc(c.state||'—')+'</td>'+
            '<td data-l="Publisher">'+fsEsc(c.publisher_sub||'—')+'</td>'+
            '<td class="n" data-l="Buyer pays">'+fsMoney(c.amount)+'</td>'+
            '<td class="n" data-l="Publisher cost">'+(c.cost_known?fsMoney(c.payout):'—')+'</td>'+
            '<td class="n '+(c.cost_known?(c.margin>=0?'fs-pos':'fs-neg'):'')+'" data-l="Margin">'+
              (c.cost_known?fsMoney(c.margin):'—')+'</td>'+
            '<td class="n" data-l="Age">'+(c.days_since_signed==null?'—':c.days_since_signed+'d')+'</td>'+
            '<td class="n" data-l="Status">'+status+'</td></tr>';
        });
        var unknown = d.filter(function(c){ return !c.cost_known; }).length;
        return '<table class="fs-t"><thead><tr><th>Lead</th><th>Phone</th><th>State</th><th>Publisher</th>'+
               '<th class="n">Buyer pays</th><th class="n">Publisher cost</th><th class="n">Margin</th>'+
               '<th class="n">Age</th><th class="n">Status</th></tr></thead><tbody>'+rows+'</tbody></table>'+
               (unknown ? '<p class="fs-note" style="padding:0 14px 10px">'+unknown+
                 ' case(s) have no publisher on record, so cost and margin cannot be worked out for them.</p>' : '');
      }

      function fsRenderBuyers(buyers, readyBuyers){
        if(!buyers.length) return fsNone('fs-buyers','No MVA money outstanding in this range.');
        var readyBy={}; readyBuyers.forEach(function(b){ readyBy[b.buyer]=b; });
        var body='', tot={ready:0,inv:0,over:0,unc:0,owed:0,cases:0};
        buyers.forEach(function(b){
          var r=readyBy[b.buyer], open=!!fsOpenBuyers[b.buyer];
          tot.ready+=b.ready; tot.inv+=b.invoiced_unpaid; tot.over+=b.overdue;
          tot.unc+=(b.unconfirmed||0); tot.owed+=b.total_owed; tot.cases+=(b.cases||0);
          body += '<tr class="'+(b.overdue>0?'late':'')+'">'+
            '<td data-l="Buyer"><button class="fs-link" onclick="fsToggleBuyer('+fsEsc(JSON.stringify(b.buyer))+')">'+
              '<span class="fs-caret">'+(open?'▾':'▸')+'</span>'+fsEsc(b.buyer)+'</button></td>'+
            '<td class="n" data-l="Cases">'+(b.cases||0)+'</td>'+
            '<td class="n" data-l="Ready">'+(b.ready?fsMoney(b.ready):'—')+'</td>'+
            '<td class="n" data-l="Invoiced">'+(b.invoiced_unpaid?fsMoney(b.invoiced_unpaid):'—')+'</td>'+
            '<td class="n" data-l="Overdue">'+(b.overdue?'<span class="fs-tag late">'+fsMoney(b.overdue)+'</span>':'—')+'</td>'+
            '<td class="n" data-l="Not confirmed">'+(b.unconfirmed?'<span class="fs-tag hold">'+fsMoney(b.unconfirmed)+'</span>':'—')+'</td>'+
            '<td class="n big" data-l="Owed">'+fsMoney(b.total_owed)+'</td>'+
            '<td class="n" data-l="">'+(r&&r.count
              ? '<button class="lx-btn sm" onclick="fsConfirmInvoice('+fsEsc(JSON.stringify(r.buyer))+')">Invoice '+r.count+'</button>'
              : '')+'</td></tr>';
          if(open) body += '<tr class="fs-detail"><td colspan="8">'+fsDetailRows(b)+'</td></tr>';
        });
        document.getElementById('fs-buyers').innerHTML = fsWrap(
          '<th>Buyer</th><th class="n">Cases</th><th class="n">Ready</th><th class="n">Invoiced</th>'+
          '<th class="n">Overdue</th><th class="n">Not confirmed</th><th class="n">Owed</th><th></th>',
          body,
          '<td data-l="">Total</td><td class="n" data-l="Cases">'+tot.cases+'</td>'+
          '<td class="n" data-l="Ready">'+fsMoney(tot.ready)+'</td>'+
          '<td class="n" data-l="Invoiced">'+fsMoney(tot.inv)+'</td>'+
          '<td class="n" data-l="Overdue">'+fsMoney(tot.over)+'</td>'+
          '<td class="n" data-l="Not confirmed">'+fsMoney(tot.unc)+'</td>'+
          '<td class="n" data-l="Owed">'+fsMoney(tot.owed)+'</td><td></td>');
      }

'''
src = src[:a] + NEW_RENDER + src[b:]

# ── 4. Styles for the clickable buyer and the expanded block ─────────────
OLD_CSS = "        .fs-pos{color:var(--lx-green)} .fs-neg{color:var(--lx-red)}"
NEW_CSS = """        .fs-pos{color:var(--lx-green)} .fs-neg{color:var(--lx-red)}
        .fs-link{font:inherit;background:none;border:0;padding:0;cursor:pointer;color:var(--lx-ink);
                 display:inline-flex;align-items:center;gap:7px;text-align:left}
        .fs-link:hover{color:var(--lx-green);text-decoration:underline}
        .fs-caret{color:var(--lx-ink-3);font-size:11px;width:9px;display:inline-block}
        .fs-detail > td{background:var(--lx-paper);padding:0 0 0 18px;border-bottom:1px solid var(--lx-line)}
        .fs-detail .fs-t{font-size:13.5px}
        .fs-detail .fs-t th{font-size:12px;padding:7px 12px}
        .fs-detail .fs-t td{padding:7px 12px}"""
if src.count(OLD_CSS) != 1:
    sys.exit("css anchor found %d times, expected 1 - aborting" % src.count(OLD_CSS))
src = src.replace(OLD_CSS, NEW_CSS, 1)

shutil.copyfile(FILE, FILE + ".pre-344.bak")
open(FILE, "w", encoding="utf-8").write(src)
print("patch 344 applied")
print("  + Cases column")
print("  + range picker (1 week / 2 weeks / Month / All time, default All)")
print("  + click a buyer to expand every case behind what they owe")
print("backup at index.html.pre-344.bak")
