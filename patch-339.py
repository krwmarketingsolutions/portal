#!/usr/bin/env python3
"""
patch-339.py  --  rebuild the MVA money section in the Leads design language,
                  add held/pending, add a P&L block

WHY IT LOOKED WRONG
The Leads page's design tokens (--lx-paper, --lx-green, the Source Serif face,
the stat cards, the section rules) are scoped to "#page-leads, #page-home,
#page-ssdi". The Invoicing page was never in that list, so the section added in
patch 337 fell back to system sans and a generic blue/amber palette and looked
like it came from a different product. It did.

THE FIX
#fs-section is added to that selector, so the section inherits the real design
system instead of imitating it. The selector is extended rather than replaced,
and the existing Trackdrive content on the same page is deliberately left out of
it, so nothing below this section changes appearance.

WHAT IS NEW
  - Four stat cards in the Leads style: ready to invoice, waiting on payment,
    overdue, and not confirmed yet.
  - HELD AND PENDING are shown (patch 338 supplies them). They are kept in their
    own card and their own column, never added into "owed", because a case you
    have held or not yet approved is not money a buyer owes you.
  - A P&L block: revenue, publisher cost and profit, by week or by month, with
    per buyer and per publisher breakdowns.

ABOUT THE P&L
It is gross margin on signed cases: what the buyer pays minus what the publisher
is paid. Ad spend and overhead are NOT in it, so it is not net profit, and the
section says so on screen rather than letting the number be misread.

Requires patch 338 on the backend. Without it the section still renders but the
held and P&L areas stay empty.

Backup: index.html.pre-339.bak    Safe to re-run: refuses twice.
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

if "patch 339" in src:
    sys.exit("patch 339 already applied - nothing to do")
if "patch 337" not in src:
    sys.exit("patch 337 is not applied - run patch-337.py first")

TOKEN_SEL = "#page-leads, #page-home, #page-ssdi{"
START = "<!-- ═══ patch 337: MVA MONEY SECTION ═══ -->"
END = "<!-- ═══ end patch 337 ═══ -->"

for name, s in (("token selector", TOKEN_SEL), ("section start", START), ("section end", END)):
    if src.count(s) != 1:
        sys.exit("%s found %d times, expected 1 - aborting, nothing changed" % (name, src.count(s)))

start_at = src.index(START)
end_at = src.index(END) + len(END)
if end_at <= start_at:
    sys.exit("section markers out of order - aborting, nothing changed")

BLOCK = r'''<!-- ═══ patch 339: MVA MONEY (Leads design language) ═══ -->
      <style>
        /* Only layout lives here. Every colour, face and rule comes from the
           Leads tokens, inherited because #fs-section joins their selector. */
        #fs-section{padding:0 40px 40px;font-family:"Source Serif 4",Georgia,"Times New Roman",serif}
        #fs-section .lx-section:first-child{margin-top:22px}
        #fs-section .lx-stats{grid-template-columns:repeat(4,1fr)}
        #fs-section .lx-stat{cursor:default}
        #fs-section .lx-stat:hover{transform:none;box-shadow:none;border-color:var(--lx-line)}
        #fs-section .lx-stat .n{font-size:34px}
        #fs-section .lx-stat.warn{border-top-color:var(--lx-brown)}
        #fs-section .lx-stat.bad{border-top-color:var(--lx-red)}
        #fs-section .lx-stat.bad .n{color:var(--lx-red)}
        #fs-section .lx-stat.muted .n{color:var(--lx-ink-2)}
        .fs-t{width:100%;border-collapse:collapse;font-size:14.5px}
        .fs-t th{text-align:left;font-weight:600;font-size:13px;color:var(--lx-ink-2);
                 padding:9px 14px;border-bottom:1px solid var(--lx-line);white-space:nowrap}
        .fs-t td{padding:10px 14px;border-bottom:1px solid var(--lx-line);vertical-align:middle}
        .fs-t tr:last-child td{border-bottom:0}
        .fs-t tbody tr:hover{background:var(--lx-paper)}
        .fs-t .n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
        .fs-t .big{font-weight:600}
        .fs-t tr.late td:first-child{box-shadow:inset 3px 0 0 var(--lx-red)}
        .fs-t tfoot td{padding:10px 14px;border-top:2px solid var(--lx-line-2);font-weight:600}
        .fs-tag{font-size:12.5px;padding:1px 8px;border-radius:2px;white-space:nowrap}
        .fs-tag.late{background:var(--lx-red-soft);color:var(--lx-red)}
        .fs-tag.ok{background:var(--lx-green-soft);color:var(--lx-green)}
        .fs-tag.hold{background:var(--lx-brown-soft);color:var(--lx-brown)}
        .fs-pos{color:var(--lx-green)} .fs-neg{color:var(--lx-red)}
        .fs-grid2{display:grid;grid-template-columns:1fr 1fr;gap:22px}
        .fs-none{padding:22px 14px;color:var(--lx-ink-3);font-size:14.5px}
        .fs-note{font-size:13px;color:var(--lx-ink-3);margin-top:8px;max-width:70ch}
        #fs-mask{display:none;position:fixed;inset:0;background:rgba(30,42,34,.42);z-index:900;
                 align-items:center;justify-content:center;padding:16px}
        #fs-mask.on{display:flex}
        #fs-mask .box{background:var(--lx-white);border:1px solid var(--lx-line-2);padding:24px;max-width:400px;width:100%;
                      font-family:"Source Serif 4",Georgia,serif;color:var(--lx-ink)}
        #fs-mask h3{font-size:20px;margin:0 0 4px;font-weight:600}
        #fs-mask p{font-size:14px;color:var(--lx-ink-2);margin:0 0 16px}
        #fs-mask dl{display:grid;grid-template-columns:auto 1fr;gap:8px 18px;margin:0 0 20px;font-size:15px}
        #fs-mask dt{color:var(--lx-ink-2)} #fs-mask dd{margin:0;text-align:right;font-variant-numeric:tabular-nums}
        #fs-mask .acts{display:flex;gap:10px;justify-content:flex-end}
        @media(max-width:820px){
          #fs-section{padding:0 18px 32px}
          #fs-section .lx-stats{grid-template-columns:1fr 1fr}
          .fs-grid2{grid-template-columns:1fr}
        }
        @media(max-width:560px){
          #fs-section .lx-stats{grid-template-columns:1fr}
          .fs-t thead{display:none}
          .fs-t tr{display:block;padding:10px 0;border-bottom:1px solid var(--lx-line)}
          .fs-t td{display:flex;justify-content:space-between;gap:16px;border:0;padding:4px 14px}
          .fs-t td:before{content:attr(data-l);color:var(--lx-ink-2);font-size:13px;flex:0 0 auto}
          .fs-t td:empty{display:none}
          .fs-t tfoot td{border:0}
        }
      </style>

      <div id="fs-section">
        <div class="lx-section">
          <div class="lx-sechead">
            <h3>MVA money</h3>
            <button class="lx-btn quiet sm" onclick="fetchFundingSummary()">Refresh</button>
          </div>
          <p class="lx-lede" id="fs-line">Loading…</p>
          <div class="lx-stats" id="fs-cards"></div>
        </div>

        <div class="lx-section">
          <div class="lx-sechead"><h3>By buyer</h3></div>
          <p class="lx-lede">What each buyer owes, and what is still waiting on your approval. Held and pending are not counted as owed.</p>
          <div class="lx-mini" id="fs-buyers"></div>
        </div>

        <div class="lx-section">
          <div class="lx-sechead"><h3>Open invoices</h3></div>
          <p class="lx-lede">Sent and not yet paid. Anything past its due date is marked late.</p>
          <div class="lx-mini" id="fs-invoices"></div>
        </div>

        <div class="lx-section">
          <div class="lx-sechead">
            <h3>Profit and loss</h3>
            <div class="lx-seg" id="fs-pnl-seg">
              <button data-p="weekly" aria-pressed="true" onclick="fsSetPnl('weekly')">Weekly</button>
              <button data-p="monthly" onclick="fsSetPnl('monthly')">Monthly</button>
            </div>
          </div>
          <p class="lx-lede">Revenue is what buyers pay on cases signed in the period. Cost is the publisher payout on those same cases.</p>
          <div class="lx-mini" id="fs-pnl"></div>
          <p class="fs-note" id="fs-pnl-basis"></p>
          <div class="fs-grid2" style="margin-top:22px">
            <div><div class="lx-sechead"><h3 style="font-size:17px">By buyer</h3></div><div class="lx-mini" id="fs-pnl-buyer"></div></div>
            <div><div class="lx-sechead"><h3 style="font-size:17px">By publisher</h3></div><div class="lx-mini" id="fs-pnl-pub"></div></div>
          </div>
        </div>

        <div class="lx-section">
          <div class="lx-sechead"><h3>Lane performance</h3></div>
          <p class="lx-lede">Margin per signed case on each publisher to buyer route, and how many leads each publisher turns into signed cases.</p>
          <div class="fs-grid2">
            <div class="lx-mini" id="fs-margins"></div>
            <div class="lx-mini" id="fs-conversion"></div>
          </div>
        </div>
      </div>

      <div id="fs-mask">
        <div class="box">
          <h3>Create invoice</h3>
          <p>This marks the cases as invoiced on your side. Nothing is emailed to the buyer.</p>
          <dl id="fs-modal-fields"></dl>
          <div class="acts">
            <button class="lx-btn quiet" onclick="fsCloseConfirm()">Cancel</button>
            <button class="lx-btn" id="fs-modal-go">Create invoice</button>
          </div>
        </div>
      </div>

      <script>
      /* patch 339 — MVA money, Leads design language. Reads GET /funding-summary. */
      var fsData = null, fsPnlMode = 'weekly';

      function fsMoney(n){ var v = Math.round(Number(n)||0); return (v<0?'-$':'$') + Math.abs(v).toLocaleString(); }
      function fsEsc(s){ return String(s==null?'':s).replace(/[&<>"']/g, function(c){
        return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
      function fsDate(d){ if(!d) return '—'; var x=new Date(d);
        return isNaN(x) ? '—' : (x.getUTCMonth()+1)+'/'+x.getUTCDate(); }
      function fsPlural(n,w){ return n+' '+w+(n===1?'':'s'); }
      function fsWeekLabel(k){ var p=String(k).split('-');
        return p.length===3 ? (Number(p[1])+'/'+Number(p[2])) : k; }
      function fsMonthLabel(k){
        var m=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        var p=String(k).split('-'); return p.length===2 ? (m[Number(p[1])-1]+' '+p[0]) : k; }

      async function fetchFundingSummary(){
        var line = document.getElementById('fs-line');
        if(!REV_API_URL || !REV_API_KEY){ if(line) line.textContent='Connect your Railway server on the Revenue tab first.'; return; }
        try{
          var res = await fetch(REV_API_URL+'/funding-summary', { headers:{'x-api-key':REV_API_KEY} });
          var d = await res.json();
          if(!d || !d.ok) throw new Error((d&&d.error)||'Bad response');
          fsData = d; renderFundingSection(d);
        }catch(err){
          if(line) line.textContent = 'Could not load: '+err.message;
        }
      }

      function renderFundingSection(d){
        var ready = d.ready_to_invoice||{total:0,by_buyer:[]};
        var wait  = d.awaiting_payment||{total:0,overdue_total:0,by_invoice:[]};
        var unc   = d.unconfirmed||{total:0,held:{total:0,count:0},pending:{total:0,count:0}};
        var rc = (ready.by_buyer||[]).reduce(function(s,b){return s+b.count;},0);

        document.getElementById('fs-cards').innerHTML =
          fsCard('Ready to invoice', ready.total, rc?fsPlural(rc,'case')+' signed and not billed':'nothing waiting', 'warn') +
          fsCard('Waiting on payment', wait.total, fsPlural((wait.by_invoice||[]).length,'invoice')+' out', '') +
          fsCard('Overdue', wait.overdue_total,
                 wait.overdue_total>0 ? ('oldest '+fsPlural(wait.oldest_overdue_days||0,'day')) : 'nothing late',
                 wait.overdue_total>0?'bad':'muted') +
          fsCard('Not confirmed yet', unc.total,
                 fsMoney(unc.held.total)+' held · '+fsMoney(unc.pending.total)+' awaiting you', 'muted');

        var top = (d.by_buyer||[])[0];
        if(!top){ document.getElementById('fs-line').textContent = 'No MVA cases signed yet.'; }
        else {
          var s = fsEsc(top.buyer)+' owes you <b>'+fsMoney(top.total_owed)+'</b>';
          if(top.ready_count) s += ', and <b>'+fsPlural(top.ready_count,'case')+'</b> of that '+
            (top.ready_count===1?'has':'have')+' not been invoiced';
          if(top.overdue>0) s += '. <b>'+fsMoney(top.overdue)+'</b> is past due';
          document.getElementById('fs-line').innerHTML = s+'.';
        }

        fsRenderBuyers(d.by_buyer||[], ready.by_buyer||[]);
        fsRenderInvoices(wait.by_invoice||[]);
        fsRenderPnl(d.pnl||null);
        fsRenderMargins(d.margins||[]);
        fsRenderConversion(d.conversion||[]);
      }

      function fsCard(label, amount, sub, cls){
        return '<div class="lx-stat '+cls+'"><div class="top"><span>'+fsEsc(label)+'</span></div>'+
               '<div class="mid"><div class="n">'+fsMoney(amount)+'</div></div>'+
               '<div class="sub">'+fsEsc(sub)+'</div></div>';
      }
      function fsWrap(head, body, foot){
        return '<table class="fs-t"><thead><tr>'+head+'</tr></thead><tbody>'+body+'</tbody>'+
               (foot?'<tfoot><tr>'+foot+'</tr></tfoot>':'')+'</table>';
      }
      function fsNone(el, msg){ document.getElementById(el).innerHTML='<div class="fs-none">'+msg+'</div>'; }

      function fsRenderBuyers(buyers, readyBuyers){
        if(!buyers.length) return fsNone('fs-buyers','No MVA money outstanding.');
        var readyBy={}; readyBuyers.forEach(function(b){ readyBy[b.buyer]=b; });
        var body='', tot={ready:0,inv:0,over:0,unc:0,owed:0};
        buyers.forEach(function(b){
          var r=readyBy[b.buyer];
          tot.ready+=b.ready; tot.inv+=b.invoiced_unpaid; tot.over+=b.overdue;
          tot.unc+=(b.unconfirmed||0); tot.owed+=b.total_owed;
          body += '<tr class="'+(b.overdue>0?'late':'')+'">'+
            '<td data-l="Buyer">'+fsEsc(b.buyer)+'</td>'+
            '<td class="n" data-l="Ready">'+(b.ready?fsMoney(b.ready):'—')+'</td>'+
            '<td class="n" data-l="Invoiced">'+(b.invoiced_unpaid?fsMoney(b.invoiced_unpaid):'—')+'</td>'+
            '<td class="n" data-l="Overdue">'+(b.overdue?'<span class="fs-tag late">'+fsMoney(b.overdue)+'</span>':'—')+'</td>'+
            '<td class="n" data-l="Not confirmed">'+(b.unconfirmed?'<span class="fs-tag hold">'+fsMoney(b.unconfirmed)+'</span>':'—')+'</td>'+
            '<td class="n big" data-l="Owed">'+fsMoney(b.total_owed)+'</td>'+
            '<td class="n" data-l="">'+(r&&r.count
              ? '<button class="lx-btn sm" onclick="fsConfirmInvoice('+fsEsc(JSON.stringify(r.buyer))+')">Invoice '+r.count+'</button>'
              : '')+'</td></tr>';
        });
        document.getElementById('fs-buyers').innerHTML = fsWrap(
          '<th>Buyer</th><th class="n">Ready</th><th class="n">Invoiced</th><th class="n">Overdue</th>'+
          '<th class="n">Not confirmed</th><th class="n">Owed</th><th></th>',
          body,
          '<td data-l="">Total</td><td class="n" data-l="Ready">'+fsMoney(tot.ready)+'</td>'+
          '<td class="n" data-l="Invoiced">'+fsMoney(tot.inv)+'</td>'+
          '<td class="n" data-l="Overdue">'+fsMoney(tot.over)+'</td>'+
          '<td class="n" data-l="Not confirmed">'+fsMoney(tot.unc)+'</td>'+
          '<td class="n" data-l="Owed">'+fsMoney(tot.owed)+'</td><td></td>');
      }

      function fsRenderInvoices(list){
        if(!list.length) return fsNone('fs-invoices','Nothing invoiced and waiting.');
        var body='';
        list.forEach(function(v){
          body += '<tr class="'+(v.overdue?'late':'')+'">'+
            '<td data-l="Invoice">'+fsEsc(v.invoice_id||'—')+'</td>'+
            '<td data-l="Buyer">'+fsEsc(v.buyer)+'</td>'+
            '<td class="n" data-l="Cases">'+v.count+'</td>'+
            '<td class="n big" data-l="Amount">'+fsMoney(v.amount)+'</td>'+
            '<td class="n" data-l="Sent">'+fsDate(v.invoiced_at)+'</td>'+
            '<td class="n" data-l="Due">'+fsDate(v.due_date)+'</td>'+
            '<td class="n" data-l="Age">'+(v.overdue
              ? '<span class="fs-tag late">'+v.days_overdue+'d late</span>'
              : '<span class="fs-tag ok">'+v.days_outstanding+'d</span>')+'</td>'+
            '<td class="n" data-l="">'+(v.invoice_id
              ? '<button class="lx-btn quiet sm" onclick="fsMarkPaid('+fsEsc(JSON.stringify(v.buyer))+')">Mark paid</button>'
              : '')+'</td></tr>';
        });
        document.getElementById('fs-invoices').innerHTML = fsWrap(
          '<th>Invoice</th><th>Buyer</th><th class="n">Cases</th><th class="n">Amount</th>'+
          '<th class="n">Sent</th><th class="n">Due</th><th class="n">Age</th><th></th>', body);
      }

      function fsSetPnl(mode){
        fsPnlMode = mode;
        var seg = document.getElementById('fs-pnl-seg');
        Array.prototype.forEach.call(seg.querySelectorAll('button'), function(b){
          b.setAttribute('aria-pressed', b.getAttribute('data-p')===mode ? 'true' : 'false');
        });
        if(fsData) fsRenderPnl(fsData.pnl);
      }

      function fsRenderPnl(p){
        document.getElementById('fs-pnl-basis').textContent = p && p.basis ? p.basis : '';
        if(!p || !(p[fsPnlMode]||[]).length) return fsNone('fs-pnl','No signed cases to report on yet.');
        var rows = p[fsPnlMode], label = fsPnlMode==='weekly' ? fsWeekLabel : fsMonthLabel;
        var body='';
        rows.forEach(function(r){
          body += '<tr>'+
            '<td data-l="'+(fsPnlMode==='weekly'?'Week of':'Month')+'">'+fsEsc(label(r.key))+'</td>'+
            '<td class="n" data-l="Cases">'+r.cases+'</td>'+
            '<td class="n" data-l="Revenue">'+fsMoney(r.revenue)+'</td>'+
            '<td class="n" data-l="Publisher cost">'+fsMoney(r.cost)+'</td>'+
            '<td class="n big '+(r.profit>=0?'fs-pos':'fs-neg')+'" data-l="Profit">'+fsMoney(r.profit)+'</td>'+
            '<td class="n" data-l="Margin">'+r.margin_pct+'%</td></tr>';
        });
        var t = p.totals||{};
        document.getElementById('fs-pnl').innerHTML = fsWrap(
          '<th>'+(fsPnlMode==='weekly'?'Week of':'Month')+'</th><th class="n">Cases</th><th class="n">Revenue</th>'+
          '<th class="n">Publisher cost</th><th class="n">Profit</th><th class="n">Margin</th>',
          body,
          '<td data-l="">All time</td><td class="n" data-l="Cases">'+(t.cases||0)+'</td>'+
          '<td class="n" data-l="Revenue">'+fsMoney(t.revenue)+'</td>'+
          '<td class="n" data-l="Publisher cost">'+fsMoney(t.cost)+'</td>'+
          '<td class="n '+((t.profit||0)>=0?'fs-pos':'fs-neg')+'" data-l="Profit">'+fsMoney(t.profit)+'</td>'+
          '<td class="n" data-l="Margin">'+(t.margin_pct||0)+'%</td>');

        var split = function(list, el, head){
          if(!list || !list.length) return fsNone(el,'Nothing yet.');
          var b='';
          list.forEach(function(r){
            b += '<tr><td data-l="'+head+'">'+fsEsc(r.key)+'</td>'+
                 '<td class="n" data-l="Cases">'+r.cases+'</td>'+
                 '<td class="n" data-l="Revenue">'+fsMoney(r.revenue)+'</td>'+
                 '<td class="n big '+(r.profit>=0?'fs-pos':'fs-neg')+'" data-l="Profit">'+fsMoney(r.profit)+'</td></tr>';
          });
          document.getElementById(el).innerHTML = fsWrap(
            '<th>'+head+'</th><th class="n">Cases</th><th class="n">Revenue</th><th class="n">Profit</th>', b);
        };
        split(p.by_buyer, 'fs-pnl-buyer', 'Buyer');
        split(p.by_publisher, 'fs-pnl-pub', 'Publisher');
      }

      function fsRenderMargins(rows){
        if(!rows.length) return fsNone('fs-margins','No signed cases yet.');
        var body='';
        rows.slice(0,8).forEach(function(m){
          body += '<tr><td data-l="Lane">'+fsEsc(m.lane)+'</td>'+
                  '<td class="n" data-l="Cases">'+m.count+'</td>'+
                  '<td class="n" data-l="Per case">'+fsMoney(m.margin_avg)+'</td>'+
                  '<td class="n big" data-l="Total">'+fsMoney(m.margin_total)+'</td></tr>';
        });
        document.getElementById('fs-margins').innerHTML = fsWrap(
          '<th>Lane</th><th class="n">Cases</th><th class="n">Per case</th><th class="n">Total</th>', body);
      }

      function fsRenderConversion(rows){
        if(!rows.length) return fsNone('fs-conversion','No leads in this window.');
        var body='';
        rows.slice(0,8).forEach(function(c){
          body += '<tr><td data-l="Publisher">'+fsEsc(c.publisher)+'</td>'+
                  '<td class="n" data-l="Sent">'+c.leads_sent+'</td>'+
                  '<td class="n" data-l="Signed">'+c.signed+'</td>'+
                  '<td class="n big" data-l="Rate">'+c.rate+'%</td></tr>';
        });
        document.getElementById('fs-conversion').innerHTML = fsWrap(
          '<th>Publisher</th><th class="n">Sent</th><th class="n">Signed</th><th class="n">Rate</th>', body);
      }

      /* Rendered field by field from the data object, never from a sentence
         built elsewhere, so what is approved is what gets sent. */
      function fsConfirmInvoice(buyer){
        if(!fsData) return;
        var b = (fsData.ready_to_invoice.by_buyer||[]).filter(function(x){ return x.buyer===buyer; })[0];
        if(!b) return;
        var due = new Date(); due.setDate(due.getDate()+3);
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
          fsCloseConfirm(); await fetchFundingSummary();
        }catch(err){ go.textContent = 'Failed: '+err.message; }
        finally{ go.disabled=false; setTimeout(function(){ go.textContent='Create invoice'; },2500); }
      }

      async function fsMarkPaid(buyer){
        if(!window.confirm('Mark every approved case for '+buyer+' as paid?')) return;
        try{
          await fetch(REV_API_URL+'/billable-queue/mark-paid', {
            method:'POST', headers:{'x-api-key':REV_API_KEY,'Content-Type':'application/json'},
            body: JSON.stringify({ buyer: buyer }) });
        }catch(err){ /* the refresh below shows the real state either way */ }
        await fetchFundingSummary();
      }

      window.addEventListener('DOMContentLoaded', function(){
        if(typeof window.showPage === 'function' && !window.__fsWrapped){
          var prev = window.showPage;
          window.showPage = function(p){
            var r = prev.apply(this, arguments);
            if(p === 'invoice'){ try{ fetchFundingSummary(); }catch(e){} }
            return r;
          };
          window.__fsWrapped = true;
        }
      });
      </script>
      <!-- ═══ end patch 339 ═══ -->'''

src = src[:start_at] + BLOCK + src[end_at:]
src = src.replace(TOKEN_SEL, "#page-leads, #page-home, #page-ssdi, #fs-section{", 1)

shutil.copyfile(FILE, FILE + ".pre-339.bak")
open(FILE, "w", encoding="utf-8").write(src)
print("patch 339 applied")
print("  + #fs-section now inherits the Leads design tokens")
print("  + held and pending shown as 'not confirmed yet'")
print("  + P&L: weekly/monthly, by buyer, by publisher")
print("backup at index.html.pre-339.bak")
print("requires patch 338 on the backend")
