#!/usr/bin/env python3
"""
patch-365.py (portal)  --  "Pending setup" stage pill colour on the onboarding tracker

Server patch 365 made pending-setup the stage right before live. The card pill
for it gets the amber-green "almost there" colour. Also bumps the build stamp.
Backup: index.html.pre-365.bak. Safe to re-run: refuses twice.
"""
import os, re, shutil, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
def find_root():
    for c in (HERE, os.path.dirname(HERE), os.getcwd(), os.path.dirname(os.getcwd()), os.path.expanduser("~/krw")):
        if os.path.isfile(os.path.join(c, "portal", "index.html")): return os.path.join(c, "portal")
        if os.path.isfile(os.path.join(c, "index.html")) and os.path.basename(c) == "portal": return c
ROOT = find_root() or sys.exit("STOPPED: run from ~/krw (needs portal/index.html)")
FILE = os.path.join(ROOT, "index.html")
src = open(FILE, encoding="utf-8").read()
if "patch 365" in src: sys.exit("patch 365 already applied - nothing to do")
OLD = "  .ob-pill.setup,.ob-pill.testing,.ob-pill.signed{background:#E4E9C7;color:#3E5A2A}"
NEW = "  .ob-pill.setup,.ob-pill.testing,.ob-pill.signed,.ob-pill.pending-setup{background:#E4E9C7;color:#3E5A2A}   /* patch 365 */"
if src.count(OLD) != 1: sys.exit("STOPPED - pill anchor found %d time(s), expected 1. Nothing changed." % src.count(OLD))
shutil.copyfile(FILE, FILE + ".pre-365.bak")
src = src.replace(OLD, NEW, 1)
stamp = time.strftime('%Y%m%d-%H%M%S')
src = re.sub(r"var KRW_BUILD = '[^']*';", "var KRW_BUILD = '" + stamp + "';", src, 1)
open(os.path.join(ROOT, 'version.txt'), 'w').write(stamp + '\n')
open(FILE, "w", encoding="utf-8").write(src)
print("Patched OK: %s (build %s)" % (FILE, stamp))
