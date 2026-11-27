#!/usr/bin/env python3
"""sim.py: the ghost fault fires at the end of an announced burst (selftest case `ghost` was red).

Usage: python3 ghost_fix_repo.py <repo checkout>
Anchored edits only: every anchor must be found exactly once, or the edit is already in.

Why: the harness waits ~400 ms for a nav entry to settle before each click of an S2 burst, but
the model ended a burst 150 ms after a click. Every click looked like a one-click burst, so a
fault that needs two clicks or more (s2:ghost) never fired."""
import ast
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "scripts/perf/sim.py"
src = path.read_text()


def sub(old, new, note):
    global src
    if new in src:
        print(f"  already in: {note}")
        return
    assert src.count(old) == 1, f"{note}: anchor found {src.count(old)} times"
    src = src.replace(old, new)
    print(f"  edited: {note}")


sub("        self.burst = (0, 0)           # (token of the last page click, clicks since the last burst ended)\n",
    "        self.burst = (0, 0)           # (token of the last page click, clicks since the last burst ended)\n"
    "        self.burst_plan = 0           # page clicks the scenario announced for the burst in progress\n",
    "SimShell keeps the announced burst length")

sub("            self.burst = (self.burst[0] + 1, self.burst[1] + 1)\n"
    "            self.at(6, self.navigate, item[len(\"perfNav_\"):])\n"
    "            self.at(150, self.end_of_burst, self.burst[0])\n",
    "            self.burst = (self.burst[0] + 1, self.burst[1] + 1)\n"
    "            self.at(6, self.navigate, item[len(\"perfNav_\"):])\n"
    "            # Without a plan the burst ends once no further click followed within 150 ms. With one\n"
    "            # it ends at the plan's last click: the harness takes ~400 ms between two clicks of a\n"
    "            # burst (it waits for the nav entry to settle), longer than any such gap.\n"
    "            if not self.burst_plan:\n"
    "                self.at(150, self.end_of_burst, self.burst[0])\n"
    "            elif self.burst[1] >= self.burst_plan:\n"
    "                self.burst_plan = 0\n"
    "                self.at(150, self.end_of_burst, self.burst[0])\n",
    "a page click ends the burst at the plan's last click")

sub("        \"\"\"No further page click followed: the burst is over. This is where a page can get stuck:\n",
    "        \"\"\"The burst is over (its last click came, or no further one followed). A page can get stuck\n",
    "end_of_burst says what it is called for")

sub("        self.log.write(f\"{time.time_ns()} @ {text}\\n\")\n",
    "        self.log.write(f\"{time.time_ns()} @ {text}\\n\")\n"
    "        if text.startswith(\"burst \"):     # \"burst about+wallpaper+about gap=60\": the clicks to come\n"
    "            self.sim.burst = (self.sim.burst[0], 0)\n"
    "            self.sim.burst_plan = len(text.split()[1].split(\"+\"))\n",
    "FakeInjector.note hands the announced burst to the model")

ast.parse(src)
path.write_text(src)
print("sim.py ok:", path)
