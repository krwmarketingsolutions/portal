#!/usr/bin/env python3
"""
patch-347.py  --  relabel for the new rule: billable is owed, approval is the portal

Patch 346 changed what pending and held mean. They now count in what a buyer
owes; approval only governs whether the payout shows on the publisher's portal.
The dashboard still said "Not confirmed yet", which now reads as the opposite
of what the number means.

  - The fourth stat card becomes "Awaiting your approval", and its subtitle
    says plainly that the money is already counted as owed and that approving
    is what updates the publisher portal.
  - The buyer table column becomes "Unapproved", for the same reason.
  - In the per-buyer drill-down, a case that has not been approved is tagged so
    it is obvious which rows are waiting on you.

Reads awaiting_approval when patch 346 is deployed and falls back to the older
`unconfirmed` key if it is not, so the page renders either way.

Backup: index.html.pre-347.bak    Safe to re-run: refuses twice.
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

if "patch 347" in src:
    sys.exit("patch 347 already applied - nothing to do")
if "patch 344" not in src:
    sys.exit("patch 344 is not applied - run patch-344.py first")

# 1. Card: read the new key, fall back to the old one, and relabel.
OLD_UNC = "        var unc   = d.unconfirmed||{total:0,held:{total:0,count:0},pending:{total:0,count:0}};"
NEW_UNC = ("        /* patch 347: patch 346 renamed this. It is owed money awaiting approval\n"
           "           for the publisher portal, not money in doubt. */\n"
           "        var unc   = d.awaiting_approval || d.unconfirmed ||\n"
           "                    {total:0,held:{total:0,count:0},pending:{total:0,count:0}};")
if src.count(OLD_UNC) != 1:
    sys.exit("unconfirmed var found %d times, expected 1 - aborting" % src.count(OLD_UNC))
src = src.replace(OLD_UNC, NEW_UNC, 1)

OLD_CARD = """          fsCard('Not confirmed yet', unc.total,
                 fsMoney(unc.held.total)+' held · '+fsMoney(unc.pending.total)+' awaiting you', 'muted');"""
NEW_CARD = """          fsCard('Awaiting your approval', unc.total,
                 'already counted as owed · approve to update the pub portal', 'warn');"""
if src.count(OLD_CARD) != 1:
    sys.exit("fourth card found %d times, expected 1 - aborting" % src.count(OLD_CARD))
src = src.replace(OLD_CARD, NEW_CARD, 1)

# 2. Buyer table column header and cell label.
OLD_TH = """'<th class="n">Overdue</th><th class="n">Not confirmed</th><th class="n">Owed</th><th></th>',"""
NEW_TH = """'<th class="n">Overdue</th><th class="n">Unapproved</th><th class="n">Owed</th><th></th>',"""
if src.count(OLD_TH) != 1:
    sys.exit("buyer header found %d times, expected 1 - aborting" % src.count(OLD_TH))
src = src.replace(OLD_TH, NEW_TH, 1)

n = src.count('data-l="Not confirmed"')
if n:
    src = src.replace('data-l="Not confirmed"', 'data-l="Unapproved"')

# 3. Tag unapproved rows in the drill-down.
OLD_STATUS = """          var status = c.overdue ? '<span class="fs-tag late">'+c.days_overdue+'d late</span>'
                     : c.invoiced ? '<span class="fs-tag ok">invoiced</span>'
                     : '<span class="fs-tag hold">not invoiced</span>';"""
NEW_STATUS = """          var status = c.overdue ? '<span class="fs-tag late">'+c.days_overdue+'d late</span>'
                     : c.invoiced ? '<span class="fs-tag ok">invoiced</span>'
                     : '<span class="fs-tag hold">not invoiced</span>';
          /* patch 347: owed either way, but this one still needs approving
             before the publisher sees the payout. */
          if (c.awaiting_approval) status += ' <span class="fs-tag hold">unapproved</span>';"""
if src.count(OLD_STATUS) != 1:
    sys.exit("detail status block found %d times, expected 1 - aborting" % src.count(OLD_STATUS))
src = src.replace(OLD_STATUS, NEW_STATUS, 1)

# 4. Section lede, which described the old behaviour.
OLD_LEDE = """          <p class="lx-lede">What each buyer owes, and what is still waiting on your approval. Held and pending are not counted as owed.</p>"""
NEW_LEDE = """          <p class="lx-lede">What each buyer owes. A case counts as owed from the moment a buyer sheet marks it billable; approving it is what puts the payout on the publisher's portal.</p>"""
if src.count(OLD_LEDE) != 1:
    sys.exit("buyer lede found %d times, expected 1 - aborting" % src.count(OLD_LEDE))
src = src.replace(OLD_LEDE, NEW_LEDE, 1)

shutil.copyfile(FILE, FILE + ".pre-347.bak")
open(FILE, "w", encoding="utf-8").write(src)
print("patch 347 applied - labels match the new rule")
print("backup at index.html.pre-347.bak")
