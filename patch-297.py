#!/usr/bin/env python3
"""
patch-297.py  --  Stop the phone (and any browser) serving a stale dashboard

THE PROBLEM
  GitHub Pages serves index.html with Cache-Control: max-age=600, and an iOS
  home-screen web app holds its last copy far longer than that while it is
  suspended. So after a fix ships, the phone can keep running yesterday's
  JavaScript with no sign anything is wrong - which is exactly how a page
  with an old bug in it kept showing "Not connected" long after the bug was
  fixed. Stale code cannot fix itself, so every such episode needed a manual
  force-quit or a cache-busting URL.

WHAT THIS ADDS
  A build stamp in the page, and a tiny version file beside it.

  The page checks version.txt (fetched with cache:'no-store', so it is never
  served from cache):
      - on load
      - whenever the tab or app regains focus - which is the moment a
        home-screen app comes back from being suspended

  If the published build differs from the one running, the page reloads
  itself once with a cache-busting parameter. One reload, guarded by a flag,
  so it can never loop.

  version.txt is 20 bytes. The check costs nothing and means the phone
  catches up on its own the moment you open it.

  Also adds no-cache meta tags, which help some browsers revalidate rather
  than serve blind from cache.

Usage (from ~/krw/portal):
    python3 patch-297.py
    git add -A && git commit -m "patch 297: page self-updates instead of serving stale" && git push

Backup: index.html.pre-297.bak. Safe to re-run; each run stamps a new build.
"""
import datetime, os, re, shutil, sys

TARGET = os.path.join(os.getcwd(), "index.html")
if not os.path.exists(TARGET):
    sys.exit("index.html not found - run this from ~/krw/portal")

src = open(TARGET, encoding="utf-8").read()
BUILD = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")

# re-running just re-stamps rather than stacking another copy
src = re.sub(r"var KRW_BUILD = '[^']*';", "var KRW_BUILD = '%s';" % BUILD, src)

if "patch 297" not in src:
    JS = """<script>
/* patch 297: the page keeps itself current.
   A home-screen app on iOS can sit on a cached copy of this file for a long
   time. version.txt is fetched with no-store so it is always the real one;
   if it does not match the build running here, reload once. */
var KRW_BUILD = '%s';
(function () {
  var reloaded = false;
  function checkBuild() {
    if (reloaded) return;
    fetch('version.txt?t=' + Date.now(), { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.text() : null; })
      .then(function (t) {
        if (!t) return;
        var latest = String(t).trim();
        if (latest && latest !== KRW_BUILD) {
          reloaded = true;                       // one reload, never a loop
          var u = location.href.split('#')[0].split('?')[0];
          location.replace(u + '?v=' + encodeURIComponent(latest));
        }
      })
      .catch(function () {});                    // offline is not an error here
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', checkBuild);
  else checkBuild();
  // the moment a suspended home-screen app comes back
  document.addEventListener('visibilitychange', function () { if (!document.hidden) checkBuild(); });
  window.addEventListener('focus', checkBuild);
})();
</script>
""" % BUILD
    m = re.search(r"<script>", src)
    if not m:
        sys.exit("no <script> tag found")
    src = src[:m.start()] + JS + src[m.start():]

    META = ('<meta http-equiv="Cache-Control" content="no-cache, must-revalidate"/>\n'
            '<meta http-equiv="Pragma" content="no-cache"/>\n')
    src = src.replace("<title>", META + "<title>", 1)

shutil.copy2(TARGET, TARGET + ".pre-297.bak")
open(TARGET, "w", encoding="utf-8").write(src)
open(os.path.join(os.getcwd(), "version.txt"), "w", encoding="utf-8").write(BUILD + "\n")

print("patch 297 applied. backup: index.html.pre-297.bak")
print("  build stamp: %s" % BUILD)
print("  version.txt written - the page now reloads itself when a newer build ships")
