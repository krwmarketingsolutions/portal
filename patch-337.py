#!/usr/bin/env python3
"""
patch-337.py  --  MVA money section on the Invoicing page

Adds a visual MVA section to the top of the existing Invoicing page, driven by
GET /funding-summary from patch 336. Patch 336 MUST be deployed first or this
section shows its error state.

WHAT IT SHOWS
  - one plain English line ("NLD owes you $18,000 across 8 signed cases")
  - three stat cards: ready to invoice / waiting on payment / overdue
  - a buyer table with a "Invoice N cases" button per buyer
  - open invoices with days outstanding, overdue first, each with Mark paid
  - margin by lane and conversion by publisher, side by side

MVA only. The existing Trackdrive/SSDI content below is untouched, and so is
fetchInvoiceData and every inv* function.

HOW IT HOOKS IN
  showPage is wrapped on DOMContentLoaded so switching to the Invoicing tab
  refreshes this section. The original function is called first and its return
  value passed through, so existing behaviour is unchanged. Nothing else in the
  page is modified.

CONFIRMATION DIALOG
  Built field by field from the data object (buyer, count, amount, due date).
  It never renders a sentence generated anywhere else, so what you approve is
  always what gets sent.

MOBILE
  Cards and tables collapse to a stacked layout under 640px. No horizontal
  scrolling. Everything is scoped under .fs- class names so nothing collides
  with the existing styles.

TRADE-OFF
  Markup, styles and script go in as one block inside #page-invoice rather than
  being split across the file. One insertion point means one thing to verify and
  one thing to reverse, at the cost of a script tag sitting mid-document.

Backup: index.html.pre-337.bak    Safe to re-run: refuses twice.
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

if "patch 337" in src:
    sys.exit("patch 337 already applied - nothing to do")

PAGE_ANCHOR = "<!-- ═══ INVOICE PAGE ═══ -->"
STRIP_ANCHOR = "<!-- SUMMARY STRIP -->"

if src.count(PAGE_ANCHOR) != 1:
    sys.exit("INVOICE PAGE anchor found %d times, expected 1 - aborting" % src.count(PAGE_ANCHOR))

page_at = src.index(PAGE_ANCHOR)
strip_at = src.find(STRIP_ANCHOR, page_at)
if strip_at < 0:
    sys.exit("no SUMMARY STRIP after the INVOICE PAGE anchor - aborting, nothing changed")
if strip_at - page_at > 4000:
    sys.exit("SUMMARY STRIP is unexpectedly far from the page anchor - aborting")

BLOCK = r'''<!-- ═══ patch 337: MVA MONEY SECTION ═══ -->
      <style>
        .fs-wrap{padding:1rem 1.25rem;border-bottom:1px solid var(--border);flex-shrink:0}
        .fs-line{font-size:14px;color:var(--text);margin-bottom:.9rem;line-height:1.5}
        .fs-line b{font-weight:600}
        .fs-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-bottom:1rem}
        .fs-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:.85rem 1rem}
        .fs-card.ready{border-left:3px solid var(--orange)}
        .fs-card.wait{border-left:3px solid var(--blue)}
        .fs-card.over{border-left:3px solid var(--red)}
        .fs-card.over.hot{background:#FDF3F3}
        .fs-k{font-family:'Helvetica Neue',Arial,sans-serif;font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:5px}
        .fs-v{font-size:22px}
        .fs-v.ready{color:var(--orange-text)} .fs-v.wait{color:var(--blue)} .fs-v.over{color:var(--red)}
        .fs-sub{font-family:'Helvetica Neue',Arial,sans-serif;font-size:11px;color:var(--muted);margin-top:2px}
        .fs-h{font-family:'Helvetica Neue',Arial,sans-serif;font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:1rem 0 .5rem}
        .fs-tbl{width:100%;border-collapse:collapse;font-family:'Helvetica Neue',Arial,sans-serif;font-size:12px}
        .fs-tbl th{text-align:left;font-weight:500;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.06em;padding:6px 8px;border-bottom:1px solid var(--border)}
        .fs-tbl td{padding:8px;border-bottom:1px solid var(--border);vertical-align:middle}
        .fs-tbl tr:last-child td{border-bottom:0}
        .fs-tbl .num{text-align:right;font-variant-numeric:tabular-nums}
        .fs-row-over{border-left:3px solid var(--red)}
        .fs-pill{display:inline-block;padding:2px 7px;border-radius:999px;font-size:10px;font-weight:500}
        .fs-pill.over{background:#F7E4E4;color:var(--red)}
        .fs-pill.ok{background:var(--green-bg);color:var(--green-text)}
        .fs-two{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
        .fs-box{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:.5rem .75rem}
        .fs-empty{font-family:'Helvetica Neue',Arial,sans-serif;font-size:12px;color:var(--muted);padding:1.25rem;text-align:center;opacity:.7}
        .fs-mask{display:none;position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:900;align-items:center;justify-content:center;padding:1rem}
        .fs-mask.on{display:flex}
        .fs-modal{background:var(--surface);border-radius:var(--radius);padding:1.25rem;max-width:380px;width:100%}
        .fs-modal h3{margin:0 0 .75rem;font-size:15px}
        .fs-modal dl{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;margin:0 0 1rem;font-family:'Helvetica Neue',Arial,sans-serif;font-size:12px}
        .fs-modal dt{color:var(--muted)} .fs-modal dd{margin:0;text-align:right;font-variant-numeric:tabular-nums}
        .fs-acts{display:flex;gap:8px;justify-content:flex-end}
        @media(max-width:640px){
          .fs-cards{grid-template-columns:1fr}
          .fs-two{grid-template-columns:1fr}
          .fs-tbl thead{display:none}
          .fs-tbl tr{display:block;border-bottom:1px solid var(--border);padding:8px 0}
          .fs-tbl td{display:flex;justify-content:space-between;gap:14px;border:0;padding:3px 8px}
          .fs-tbl td:before{content:attr(data-l);color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.06em;flex:0 0 auto;white-space:nowrap}
          .fs-tbl td:empty{display:none}
          .fs-tbl .num{text-align:right}
        }
      </style>

      <div class="fs-wrap" id="fs-section">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:.6rem">
          <span class="fs-h" style="margin:0">MVA money</span>
          <div style="flex:1"></div>
          <button class="inv-refresh-btn" onclick="fetchFundingSummary()">↻ Refresh</button>
        </div>
        <div class="fs-line" id="fs-line">Loading…</div>
        <div class="fs-cards">
          <div class="fs-card ready"><div class="fs-k">Ready to invoice</div><div class="fs-v ready" id="fs-ready">$0</div><div class="fs-sub" id="fs-ready-sub">—</div></div>
          <div class="fs-card wait"><div class="fs-k">Waiting on payment</div><div class="fs-v wait" id="fs-wait">$0</div><div class="fs-sub" id="fs-wait-sub">—</div></div>
          <div class="fs-card over" id="fs-over-card"><div class="fs-k">Overdue</div><div class="fs-v over" id="fs-over">$0</div><div class="fs-sub" id="fs-over-sub">—</div></div>
        </div>
        <div class="fs-h">By buyer</div>
        <div id="fs-buyers"></div>
        <div class="fs-h">Open invoices</div>
        <div id="fs-invoices"></div>
        <div class="fs-two">
          <div><div class="fs-h">Margin by lane</div><div class="fs-box" id="fs-margins"></div></div>
          <div><div class="fs-h">Conversion</div><div class="fs-box" id="fs-conversion"></div></div>
        </div>
      </div>

      <div class="fs-mask" id="fs-mask">
        <div class="fs-modal">
          <h3 id="fs-modal-title">Create invoice</h3>
          <dl id="fs-modal-fields"></dl>
          <div class="fs-acts">
            <button class="btn" onclick="fsCloseConfirm()">Cancel</button>
            <button class="btn btn-green" id="fs-modal-go">Create invoice</button>
          </div>
        </div>
      </div>

      <script>
      /* patch 337 — MVA money section. Reads GET /funding-summary (patch 336). */
      var fsData = null;

      function fsMoney(n){ return '$' + Math.round(Number(n)||0).toLocaleString(); }
      function fsEsc(s){ return String(s==null?'':s).replace(/[&<>"']/g, function(c){
        return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
      function fsDate(d){ if(!d) return '—'; var x=new Date(d);
        return isNaN(x) ? '—' : (x.getUTCMonth()+1)+'/'+x.getUTCDate(); }
      function fsPlural(n,w){ return n+' '+w+(n===1?'':'s'); }

      async function fetchFundingSummary(){
        var line = document.getElementById('fs-line');
        if(!REV_API_URL || !REV_API_KEY){ if(line) line.textContent='Connect your Railway server on the Revenue tab first.'; return; }
        try{
          var res = await fetch(REV_API_URL+'/funding-summary', { headers:{'x-api-key':REV_API_KEY} });
          var d = await res.json();
          if(!d || !d.ok) throw new Error((d&&d.error)||'Bad response');
          fsData = d;
          renderFundingSection(d);
        }catch(err){
          if(line) line.textContent = 'Could not load: '+err.message+(String(err.message).indexOf('404')>-1?' (is patch 336 deployed?)':'');
        }
      }

      function renderFundingSection(d){
        var ready = d.ready_to_invoice||{total:0,by_buyer:[]};
        var wait  = d.awaiting_payment||{total:0,overdue_total:0,by_invoice:[]};

        document.getElementById('fs-ready').textContent = fsMoney(ready.total);
        var rc = (ready.by_buyer||[]).reduce(function(s,b){return s+b.count;},0);
        document.getElementById('fs-ready-sub').textContent =
          rc ? fsPlural(rc,'case')+' across '+fsPlural((ready.by_buyer||[]).length,'buyer') : 'nothing waiting';

        document.getElementById('fs-wait').textContent = fsMoney(wait.total);
        document.getElementById('fs-wait-sub').textContent = fsPlural((wait.by_invoice||[]).length,'invoice')+' out';

        document.getElementById('fs-over').textContent = fsMoney(wait.overdue_total);
        document.getElementById('fs-over-sub').textContent =
          wait.overdue_total>0 ? ('oldest '+fsPlural(wait.oldest_overdue_days||0,'day')) : 'nothing late';
        document.getElementById('fs-over-card').className = 'fs-card over'+(wait.overdue_total>0?' hot':'');

        /* Plain English line, built from the biggest single thing owed. */
        var top = (d.by_buyer||[])[0];
        if(!top){ document.getElementById('fs-line').textContent = 'No MVA cases signed yet.'; }
        else {
          var bits = fsEsc(top.buyer)+' owes you <b>'+fsMoney(top.total_owed)+'</b>';
          if(top.ready_count) bits += ', and <b>'+fsPlural(top.ready_count,'case')+'</b> of that '+
            (top.ready_count===1?'is':'are')+' not invoiced yet';
          if(top.overdue>0)   bits += '. <b>'+fsMoney(top.overdue)+'</b> is past due';
          document.getElementById('fs-line').innerHTML = bits+'.';
        }

        fsRenderBuyers(d.by_buyer||[], ready.by_buyer||[]);
        fsRenderInvoices(wait.by_invoice||[]);
        fsRenderMargins(d.margins||[]);
        fsRenderConversion(d.conversion||[]);
      }

      function fsRenderBuyers(buyers, readyBuyers){
        var el = document.getElementById('fs-buyers');
        if(!buyers.length){ el.innerHTML = '<div class="fs-empty">No MVA money outstanding.</div>'; return; }
        var readyBy = {}; readyBuyers.forEach(function(b){ readyBy[b.buyer]=b; });
        var h = '<table class="fs-tbl"><thead><tr><th>Buyer</th><th class="num">Ready</th>'+
                '<th class="num">Invoiced</th><th class="num">Overdue</th><th class="num">Owed</th><th></th></tr></thead><tbody>';
        buyers.forEach(function(b){
          var r = readyBy[b.buyer];
          h += '<tr class="'+(b.overdue>0?'fs-row-over':'')+'">'+
            '<td data-l="Buyer">'+fsEsc(b.buyer)+'</td>'+
            '<td class="num" data-l="Ready">'+(b.ready?fsMoney(b.ready):'—')+'</td>'+
            '<td class="num" data-l="Invoiced">'+(b.invoiced_unpaid?fsMoney(b.invoiced_unpaid):'—')+'</td>'+
            '<td class="num" data-l="Overdue">'+(b.overdue?'<span class="fs-pill over">'+fsMoney(b.overdue)+'</span>':'—')+'</td>'+
            '<td class="num" data-l="Owed"><b>'+fsMoney(b.total_owed)+'</b></td>'+
            '<td class="num" data-l="">'+(r&&r.count
              ? '<button class="btn btn-green" style="font-size:11px;padding:3px 9px" onclick="fsConfirmInvoice('+fsEsc(JSON.stringify(r.buyer))+')">Invoice '+r.count+'</button>'
              : '')+'</td></tr>';
        });
        el.innerHTML = h+'</tbody></table>';
      }

      function fsRenderInvoices(list){
        var el = document.getElementById('fs-invoices');
        if(!list.length){ el.innerHTML = '<div class="fs-empty">Nothing invoiced and waiting.</div>'; return; }
        var h = '<table class="fs-tbl"><thead><tr><th>Invoice</th><th>Buyer</th><th class="num">Amount</th>'+
                '<th class="num">Sent</th><th class="num">Due</th><th class="num">Age</th><th></th></tr></thead><tbody>';
        list.forEach(function(v){
          h += '<tr class="'+(v.overdue?'fs-row-over':'')+'">'+
            '<td data-l="Invoice" style="font-size:11px">'+fsEsc(v.invoice_id||'—')+'</td>'+
            '<td data-l="Buyer">'+fsEsc(v.buyer)+'</td>'+
            '<td class="num" data-l="Amount">'+fsMoney(v.amount)+'</td>'+
            '<td class="num" data-l="Sent">'+fsDate(v.invoiced_at)+'</td>'+
            '<td class="num" data-l="Due">'+fsDate(v.due_date)+'</td>'+
            '<td class="num" data-l="Age">'+(v.overdue
              ? '<span class="fs-pill over">'+v.days_overdue+'d late</span>'
              : '<span class="fs-pill ok">'+v.days_outstanding+'d</span>')+'</td>'+
            '<td class="num" data-l="">'+(v.invoice_id
              ? '<button class="btn" style="font-size:11px;padding:3px 9px" onclick="fsMarkPaid('+fsEsc(JSON.stringify(v.buyer))+')">Mark paid</button>'
              : '')+'</td></tr>';
        });
        el.innerHTML = h+'</tbody></table>';
      }

      function fsRenderMargins(rows){
        var el = document.getElementById('fs-margins');
        if(!rows.length){ el.innerHTML = '<div class="fs-empty">No signed cases yet.</div>'; return; }
        var h = '<table class="fs-tbl"><thead><tr><th>Lane</th><th class="num">Cases</th><th class="num">Avg</th><th class="num">Total</th></tr></thead><tbody>';
        rows.slice(0,8).forEach(function(m){
          h += '<tr><td data-l="Lane" style="font-size:11px">'+fsEsc(m.lane)+'</td>'+
               '<td class="num" data-l="Cases">'+m.count+'</td>'+
               '<td class="num" data-l="Avg">'+fsMoney(m.margin_avg)+'</td>'+
               '<td class="num" data-l="Total"><b>'+fsMoney(m.margin_total)+'</b></td></tr>';
        });
        el.innerHTML = h+'</tbody></table>';
      }

      function fsRenderConversion(rows){
        var el = document.getElementById('fs-conversion');
        if(!rows.length){ el.innerHTML = '<div class="fs-empty">No leads in this window.</div>'; return; }
        var h = '<table class="fs-tbl"><thead><tr><th>Publisher</th><th class="num">Sent</th><th class="num">Signed</th><th class="num">Rate</th></tr></thead><tbody>';
        rows.slice(0,8).forEach(function(c){
          h += '<tr><td data-l="Publisher" style="font-size:11px">'+fsEsc(c.publisher)+'</td>'+
               '<td class="num" data-l="Sent">'+c.leads_sent+'</td>'+
               '<td class="num" data-l="Signed">'+c.signed+'</td>'+
               '<td class="num" data-l="Rate"><b>'+c.rate+'%</b></td></tr>';
        });
        el.innerHTML = h+'</tbody></table>';
      }

      /* Confirmation is built field by field from the data object, never from
         a sentence generated elsewhere, so what you approve is what is sent. */
      function fsConfirmInvoice(buyer){
        if(!fsData) return;
        var b = (fsData.ready_to_invoice.by_buyer||[]).filter(function(x){ return x.buyer===buyer; })[0];
        if(!b) return;
        var due = new Date(); due.setDate(due.getDate()+3);
        document.getElementById('fs-modal-title').textContent = 'Create invoice';
        document.getElementById('fs-modal-fields').innerHTML =
          '<dt>Buyer</dt><dd>'+fsEsc(b.buyer)+'</dd>'+
          '<dt>Cases</dt><dd>'+b.count+'</dd>'+
          '<dt>Amount</dt><dd><b>'+fsMoney(b.amount)+'</b></dd>'+
          '<dt>Terms</dt><dd>net 3</dd>'+
          '<dt>Due</dt><dd>'+(due.getMonth()+1)+'/'+due.getDate()+'</dd>';
        document.getElementById('fs-modal-go').onclick = function(){ fsDoInvoice(b.buyer); };
        document.getElementById('fs-mask').classList.add('on');
      }
      function fsCloseConfirm(){ document.getElementById('fs-mask').classList.remove('on'); }

      async function fsDoInvoice(buyer){
        var go = document.getElementById('fs-modal-go');
        go.disabled = true; go.textContent = 'Creating…';
        try{
          var res = await fetch(REV_API_URL+'/billable-queue/invoice', {
            method:'POST', headers:{'x-api-key':REV_API_KEY,'Content-Type':'application/json'},
            body: JSON.stringify({ buyer: buyer, terms_days: 3 }) });
          var d = await res.json();
          if(!d || !d.ok) throw new Error((d&&d.error)||'Failed');
          fsCloseConfirm();
          await fetchFundingSummary();
        }catch(err){
          go.textContent = 'Failed: '+err.message;
        }finally{
          go.disabled = false;
          setTimeout(function(){ go.textContent='Create invoice'; }, 2500);
        }
      }

      async function fsMarkPaid(buyer){
        if(!window.confirm('Mark every approved case for '+buyer+' as paid?')) return;
        try{
          await fetch(REV_API_URL+'/billable-queue/mark-paid', {
            method:'POST', headers:{'x-api-key':REV_API_KEY,'Content-Type':'application/json'},
            body: JSON.stringify({ buyer: buyer }) });
          await fetchFundingSummary();
        }catch(err){ /* summary refresh below shows the real state */ }
      }

      /* Refresh when the Invoicing tab opens. Wraps showPage additively: the
         original runs first and its return value is passed through. */
      window.addEventListener('DOMContentLoaded', function(){
        if(typeof window.showPage === 'function' && !window.__fsWrapped){
          var prev = window.showPage;
          window.showPage = function(p){
            var r = prev.apply(this, arguments);
            if(p === 'invoice') { try{ fetchFundingSummary(); }catch(e){} }
            return r;
          };
          window.__fsWrapped = true;
        }
      });
      </script>
      <!-- ═══ end patch 337 ═══ -->

      '''

src = src[:strip_at] + BLOCK + src[strip_at:]

shutil.copyfile(FILE, FILE + ".pre-337.bak")
open(FILE, "w", encoding="utf-8").write(src)
print("patch 337 applied - MVA money section added to the Invoicing page")
print("backup at index.html.pre-337.bak")
print("requires patch 336 deployed on the backend")
print("commit and push the portal repo to publish")
