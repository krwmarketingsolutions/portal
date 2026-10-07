#!/usr/bin/env python3
"""
patch-296.py  --  The dashboard showed zeros because an empty key is falsy

THE BUG (mine, from patch 289)
  Patch 289 removed the hardcoded admin key by setting it to an empty string:

      var REV_API_KEY = '';
      var OR_API_KEY_ = '';

  But this page does not use that variable only as a header value - it uses it
  38 separate times as an "are we configured?" flag:

      async function fetchLeadsSummary(){
        if(!window.REV_API_URL||!window.REV_API_KEY) return;   // <- bails
        ...
      async function fetchLeadsFeed(){
        if(!window.REV_API_URL||!window.REV_API_KEY){
          ...lxSetLive('', 'Not connected');                   // <- the badge
          return;

  An empty string is falsy, so every one of those 38 functions returned before
  making a request. No request, no error, no console message - just a fully
  rendered dashboard full of zeros and "Not connected". The backend was fine
  the whole time and the login token was fine the whole time; the page simply
  never asked.

  Verified live in Kyler's own browser: setting the variable to any truthy
  value made the data appear immediately (18 leads, 78% forwarded, badge
  cleared) with no other change.

THE FIX
  Give both variables a truthy sentinel instead of an empty string. The
  value is never a credential and never leaves the browser: the patch 289
  fetch interceptor deletes the x-api-key header and attaches
  Authorization: Bearer <login token> on every call to the backend. The
  sentinel exists purely so those 38 guards read "configured".

  Checked: this page makes no XMLHttpRequest calls, so every request really
  does go through the interceptor.
"""
import os, re, shutil, sys

TARGET = os.path.join(os.getcwd(), "index.html")
if not os.path.exists(TARGET):
    sys.exit("index.html not found - run this from ~/krw/portal")

src = open(TARGET, encoding="utf-8").read()
if "patch 296" in src:
    sys.exit("patch 296 already applied - nothing to do")

SENTINEL = "via-login-token"
NOTE = ("   // patch 296: MUST be truthy - 38 guards read this as "
        "\"configured\". Not a credential; the interceptor swaps in the login token.")

pairs = [
    ("var OR_API_KEY_='';   // patch 289: the token does this now",
     "var OR_API_KEY_='%s';%s" % (SENTINEL, NOTE)),
    ("var REV_API_KEY = '';   // patch 289: the token does this now",
     "var REV_API_KEY = '%s';%s" % (SENTINEL, NOTE)),
]
done = 0
for old, new in pairs:
    if src.count(old) == 1:
        src = src.replace(old, new, 1); done += 1
    else:
        sys.exit("could not find: %s" % old[:40])

shutil.copy2(TARGET, TARGET + ".pre-296.bak")
open(TARGET, "w", encoding="utf-8").write(src)
print("patch 296 applied. backup: index.html.pre-296.bak")
print("  %d key variables given a truthy sentinel" % done)
print("  the real credential is still the login token, attached by the interceptor")
