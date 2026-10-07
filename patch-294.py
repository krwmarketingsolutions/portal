#!/usr/bin/env python3
"""
patch-294.py  --  Make the dashboard say what is wrong instead of showing zeros

THE BUG (mine, from patch 289)
  On load the page checks its saved token:

      fetch('.../auth/check')
        .then(...)            # a bad token -> shows the login. fine.
        .catch(function () {});   # <-- anything else -> DOES NOTHING

  If that check errors for any reason - network blip, CORS, server
  restarting - the page silently keeps a token the server will not accept.
  No login box, no error. Every data call then 401s and the dashboard shows
  "Not connected" and a wall of zeros, which is indistinguishable from the
  backend being down. There was also nothing watching the data calls, so a
  token that expired mid-session produced the same silent zeros.

WHAT THIS FIXES
  1. The swallowed error now shows the login with a reason, instead of
     nothing.
  2. The fetch interceptor watches every backend response. The first 401 or
     403 clears the stored token and brings up the login. The dashboard can
     no longer sit on a dead session.
  3. Adding ?signout to the URL forces a clean sign-in - a recovery route
     that needs no developer console.
  4. The login box reports the real reason it appeared: expired session,
     server unreachable, or just signed out.

Usage (from ~/krw/portal):
    python3 patch-294.py
    git add -A && git commit -m "patch 294: dashboard recovers from a dead session" && git push

Backup: index.html.pre-294.bak. Safe to re-run.
"""
import os, shutil, sys

TARGET = os.path.join(os.getcwd(), "index.html")
if not os.path.exists(TARGET):
    TARGET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
if not os.path.exists(TARGET):
    sys.exit("index.html not found - run this from ~/krw/portal")

src = open(TARGET, encoding="utf-8").read()
if "patch 294" in src:
    sys.exit("patch 294 already applied - nothing to do")

# ---- 1. gate(): never swallow the failure -----------------------------------
OLD_GATE = """  function gate() {
    if (!KRW_TOKEN) { krwShowLogin(''); return; }
    fetch('https://' + KRW_API_HOST + '/auth/check')
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j.ok || j.role !== 'admin') { KRW_TOKEN = ''; krwShowLogin('That session expired. Sign in again.'); }
        else krwLoadConfig();
      })
      .catch(function () {});
  }"""

NEW_GATE = """  function gate() {
    // patch 294: ?signout forces a clean sign-in without the dev console
    if (location.search.indexOf('signout') > -1) {
      try { localStorage.removeItem('krw_token'); } catch (e) {}
      KRW_TOKEN = ''; krwShowLogin('Signed out. Sign in to load your data.'); return;
    }
    if (!KRW_TOKEN) { krwShowLogin(''); return; }
    fetch('https://' + KRW_API_HOST + '/auth/check')
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j.ok || j.role !== 'admin') { krwDropToken('That session expired. Sign in again.'); }
        else krwLoadConfig();
      })
      // patch 294: this used to be an empty catch, which left the page sitting
      // on a token the server rejects - no login, no error, just zeros.
      .catch(function (e) {
        krwShowLogin('Could not reach the server to check your session. '
          + 'If this keeps happening, sign in again.');
      });
  }"""

if src.count(OLD_GATE) != 1:
    sys.exit("gate() does not look the way patch 294 expects - aborting, index.html untouched")
src = src.replace(OLD_GATE, NEW_GATE, 1)

# ---- 2. interceptor: a 401/403 anywhere ends the session --------------------
OLD_FETCH = """(function () {
  var _fetch = window.fetch;
  window.fetch = function (url, opts) {
    try {
      if (String(url).indexOf(KRW_API_HOST) > -1 && KRW_TOKEN) {
        opts = opts || {};
        var h = {};
        if (opts.headers) { for (var k in opts.headers) h[k] = opts.headers[k]; }
        h['Authorization'] = 'Bearer ' + KRW_TOKEN;
        delete h['x-api-key'];
        opts.headers = h;
      }
    } catch (e) {}
    return _fetch.call(this, url, opts);
  };
})();"""

NEW_FETCH = """// patch 294: drop a dead session and ask for a sign-in, rather than
// letting every call fail quietly behind a dashboard full of zeros.
function krwDropToken(msg) {
  try { localStorage.removeItem('krw_token'); } catch (e) {}
  KRW_TOKEN = '';
  krwShowLogin(msg || 'That session expired. Sign in again.');
}
(function () {
  var _fetch = window.fetch;
  window.fetch = function (url, opts) {
    var isApi = false;
    try {
      isApi = String(url).indexOf(KRW_API_HOST) > -1;
      if (isApi && KRW_TOKEN) {
        opts = opts || {};
        var h = {};
        if (opts.headers) { for (var k in opts.headers) h[k] = opts.headers[k]; }
        h['Authorization'] = 'Bearer ' + KRW_TOKEN;
        delete h['x-api-key'];
        opts.headers = h;
      }
    } catch (e) {}
    var p = _fetch.call(this, url, opts);
    if (!isApi) return p;
    return p.then(function (r) {
      // one 401/403 means this token is finished - say so immediately
      if ((r.status === 401 || r.status === 403) && KRW_TOKEN
          && String(url).indexOf('/auth/login') < 0) {
        krwDropToken('Your session is no longer valid. Sign in again.');
      }
      return r;
    });
  };
})();"""

if src.count(OLD_FETCH) != 1:
    sys.exit("the fetch interceptor does not look the way patch 294 expects - aborting")
src = src.replace(OLD_FETCH, NEW_FETCH, 1)

shutil.copy2(TARGET, TARGET + ".pre-294.bak")
open(TARGET, "w", encoding="utf-8").write(src)
print("patch 294 applied. backup: index.html.pre-294.bak")
print("  gate() no longer swallows a failed session check")
print("  any 401/403 from the backend now ends the session and shows the login")
print("  ?signout added as a recovery route")
