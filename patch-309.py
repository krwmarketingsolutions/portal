#!/usr/bin/env python3
"""
patch-309.py  --  Funnel page draws live lines from REAL flow (pairs with 308)

WHAT CHANGES (portal/funnel.html only)
  The green "Live routing" lines were drawn from the static routing map -
  every buyer a publisher COULD reach got a line, whether or not any lead
  flowed. Now they are drawn from the endpoint's new `edges` data (patch
  308): a green line appears only between a publisher and a buyer that
  actually exchanged leads in the selected period, and the line gets
  thicker with volume. A quiet period shows no green lines, which is the
  truth. Planned (amber) lines are untouched.

Usage (from ~/krw/portal):
    python3 patch-309.py
    git add -A && git commit -m "patch 309: funnel lines = real flow" && git push

Backup: funnel.html.pre-309.bak. Safe to re-run.
"""
import os, shutil, sys

TARGET = "funnel.html"
if not os.path.exists(TARGET):
    sys.exit("funnel.html not found - run this from ~/krw/portal")

src = open(TARGET, encoding="utf-8").read()
if "patch 309" in src:
    sys.exit("patch 309 already applied - nothing to do")

OLD = """  // Live (auto) routing lines - not removable, always reflect real system state
  pubIds.forEach(function(pubId){
    var reachable = routing[pubId] || [];
    reachable.forEach(function(buyerName){
      var d = pathFor(pubId, buyerName);
      if (d) markup += '<path class="flow-path" d="' + d + '"/>';
    });
  });"""

if src.count(OLD) != 1:
    sys.exit("the live-lines block does not look the way patch 309 expects - aborting, funnel.html untouched")

NEW = """  // patch 309: live lines come from data.edges - the leads that ACTUALLY
  // flowed publisher -> buyer in the selected period (patch 308 server-side).
  // The old behavior drew the static routing capability map, so the page
  // showed "live" lines for buyers that received nothing. Line width scales
  // with volume; a quiet period shows no green lines, which is the truth.
  var edges = data.edges || {};
  pubIds.forEach(function(pubId){
    var m = edges[pubId] || {};
    Object.keys(m).forEach(function(buyerName){
      var n = m[buyerName] || 0;
      if (!n) return;
      var d = pathFor(pubId, buyerName);
      if (!d) return;
      var w = Math.min(5, 1.6 + Math.log(n + 1));
      markup += '<path class="flow-path" style="stroke-width:' + w + '" data-count="' + n + '" d="' + d + '"/>';
    });
  });"""

src = src.replace(OLD, NEW, 1)
shutil.copy2(TARGET, TARGET + ".pre-309.bak")
open(TARGET, "w", encoding="utf-8").write(src)
print("patch 309 applied. backup: funnel.html.pre-309.bak")
print("  green lines now mean leads actually moved on that path in the period")
