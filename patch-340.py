#!/usr/bin/env python3
"""
patch-340.py  --  let the Invoicing page scroll

THE BUG
#page-invoice is a fixed-height flex column with overflow-y:hidden. That was
fine when the page held only the Trackdrive view, because its inner panes did
their own scrolling. The MVA money section added in patch 339 is a plain block
in that column, so once its content is taller than the window the overflow is
clipped with no way to reach it. On a laptop that cuts off at the P&L.

Nothing was wrong with the section itself; it was never reachable.

THE FIX
Two changes, both applied at runtime so no existing markup is rewritten:

  1. #page-invoice gets overflow-y:auto, so the page scrolls as one document
     with one scrollbar, which is what the rest of the dashboard does.

  2. The Trackdrive body below (the div with inline flex:1 / overflow:hidden)
     asked for a full flex share of what was a non-scrolling column. In a
     scrolling column that makes it collapse toward zero. It is pinned to
     flex:0 0 auto with a 420px floor instead, so it keeps a usable height and
     its own inner lists still scroll exactly as before.

Verified on the live page before writing: with the change the container reports
scrollHeight 786 against clientHeight 760 and scrolls, and the Trackdrive
summary stays rendered.

The function is idempotent (a data-fs-scroll flag) and only ever touches a
sibling whose inline style is exactly flex:1 with overflow:hidden, so if that
markup is ever rewritten this quietly does nothing rather than mangling it.

Backup: index.html.pre-340.bak    Safe to re-run: refuses twice.
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

if "patch 340" in src:
    sys.exit("patch 340 already applied - nothing to do")
if "patch 339" not in src:
    sys.exit("patch 339 is not applied - run patch-339.py first")

# Insert the helper just before the render entry point, and call it from there.
ANCHOR = "      function renderFundingSection(d){"
CALL_AFTER = "        fsRenderConversion(d.conversion||[]);\n      }"

for name, s in (("render function", ANCHOR), ("render tail", CALL_AFTER)):
    if src.count(s) != 1:
        sys.exit("%s found %d times, expected 1 - aborting, nothing changed" % (name, src.count(s)))

HELPER = r'''      /* patch 340: the Invoicing page is a fixed-height flex column with
         overflow-y:hidden, so this section's content was clipped with no way
         to scroll to it. Let the page scroll as one document, and stop the
         Trackdrive body below from claiming a full flex share of a scrolling
         column (which would collapse it). Idempotent; leaves the markup alone
         if it is ever rewritten. */
      function fsEnablePageScroll(){
        var pg = document.getElementById('page-invoice');
        if(!pg || pg.getAttribute('data-fs-scroll')) return;
        pg.style.overflowY = 'auto';
        Array.prototype.forEach.call(pg.children, function(c){
          if(c.style && c.style.flex === '1' && c.style.overflow === 'hidden'){
            c.style.flex = '0 0 auto';
            if(!c.style.minHeight || c.style.minHeight === '0px') c.style.minHeight = '420px';
          }
        });
        pg.setAttribute('data-fs-scroll','1');
      }

'''

NEW_TAIL = (
    "        fsRenderConversion(d.conversion||[]);\n"
    "        fsEnablePageScroll();\n"
    "      }"
)

src = src.replace(ANCHOR, HELPER + ANCHOR, 1)
src = src.replace(CALL_AFTER, NEW_TAIL, 1)

# Also run it when the tab is opened, so an empty or failed load still scrolls.
HOOK = "            if(p === 'invoice'){ try{ fetchFundingSummary(); }catch(e){} }"
if src.count(HOOK) == 1:
    src = src.replace(
        HOOK,
        "            if(p === 'invoice'){ try{ fsEnablePageScroll(); fetchFundingSummary(); }catch(e){} }",
        1)
else:
    sys.exit("showPage hook not found exactly once - aborting, nothing changed")

shutil.copyfile(FILE, FILE + ".pre-340.bak")
open(FILE, "w", encoding="utf-8").write(src)
print("patch 340 applied - Invoicing page scrolls as one document")
print("backup at index.html.pre-340.bak")
