#!/usr/bin/env python3
"""S1/S3 harness fixes, as anchored edits on the repo checkout (anchors of 9a81fbd).

Run on the host from scripts/perf of the repo checkout:  python3 /tmp/s1s3_patch_repo.py
Idempotent: a file that already carries an edit is left alone. Every anchor must exist
exactly once; a drifted anchor stops the script before anything is written.

Why (first live S1/S3 run, 2026-11-27 11:22, p-head):
  - the panel stage glides in (SlideLoader) while open_control() already returned: the first
    click of ordered rep 1 landed on the backdrop 127 ms after the open (`closePanels open`),
    the panel closed, and the 11 clicks that followed went to the desktop for 128 s;
  - the probe's `cc.tab` mark read `root.selectedTab` inside onCurrentTabChanged, where that
    binding still named the tab being left: every S1 reaction time was None;
  - the S3 workspace round left the owner's EMPTY workspace (niri drops it as soon as it loses
    the focus): workspace id 4 became id 5 at the same index, and `restored` compared indices;
  - S1 reopened the Control Center after its last rep, so every scenario that followed began
    with a recovery ("a panel was still open before the cycle");
  - the probe placed a Control (LiquidButton is one) by adding x/y up the parent chain, which
    ignores the stage's Translate transform: while the panel glides in, a tab's rect never
    moves. A Control now maps through the part that fills it, so "the rect has stopped" is
    true evidence; still_item_point records its reads (meta.still_reads).
"""
import ast

CHANGED = []


def sub(src, old, new, note, optional=False):
    # The whole new text in the file means the edit is done. (`old` may be part of `new`: an
    # insertion keeps its anchor, so "old is gone" is no proof of anything.)
    if new in src:
        return src
    if optional and old not in src:
        return src                # a migration step: nothing of the older text is there
    assert src.count(old) == 1, f"anchor not unique ({src.count(old)}x): {note}"
    CHANGED.append(note)
    return src.replace(old, new, 1)


# ---- scenarios.py ---------------------------------------------------------------------------
src = open("scenarios.py").read()

# still_item_point, final text. It also says how many reads it took and how far the item had
# still been travelling (meta.still_reads): the evidence that the stage was gliding.
NEW_STILL = (
    "        last = first = None\n"
    "        for reads in range(1, rounds + 1):\n"
    "            try:\n"
    "                rect = self.probe.rect(name)\n"
    "            except ProbeError as error:\n"
    "                self.problems.append({\"t\": round(self.now(), 3), \"probe\": f\"rect {name}\",\n"
    "                                      \"error\": str(error)[:240]})\n"
    "                return None\n"
    "            if not rect.get(\"found\") or not rect.get(\"shown\"):\n"
    "                return None\n"
    "            if first is None:\n"
    "                first = rect\n"
    "            if last is not None and abs(rect[\"x\"] - last[\"x\"]) < 0.5 and abs(rect[\"y\"] - last[\"y\"]) < 0.5:\n"
    "                self.sleep(rest_ms)\n"
    "                moved = ((rect[\"x\"] - first[\"x\"]) ** 2 + (rect[\"y\"] - first[\"y\"]) ** 2) ** 0.5\n"
    "                self.meta.setdefault(\"still_reads\", []).append(\n"
    "                    {\"t\": round(self.now(), 3), \"item\": name, \"reads\": reads, \"moved_px\": round(moved, 2)})\n"
    "                return rect[\"x\"], rect[\"y\"]\n"
    "            last = rect\n"
    "            self.sleep(step_ms)\n"
    "        return None\n")

# c2e51ba wrote still_item_point without its read log; a tree that carries it is brought up
# to the text above (a tree from 9a81fbd gets the final text from the insertion further down).
OLD_STILL_V1 = (
    "        last = None\n"
    "        for _ in range(rounds):\n"
    "            try:\n"
    "                rect = self.probe.rect(name)\n"
    "            except ProbeError as error:\n"
    "                self.problems.append({\"t\": round(self.now(), 3), \"probe\": f\"rect {name}\",\n"
    "                                      \"error\": str(error)[:240]})\n"
    "                return None\n"
    "            if not rect.get(\"found\") or not rect.get(\"shown\"):\n"
    "                return None\n"
    "            if last is not None and abs(rect[\"x\"] - last[\"x\"]) < 0.5 and abs(rect[\"y\"] - last[\"y\"]) < 0.5:\n"
    "                self.sleep(rest_ms)\n"
    "                return rect[\"x\"], rect[\"y\"]\n"
    "            last = rect\n"
    "            self.sleep(step_ms)\n"
    "        return None\n")
src = sub(src, OLD_STILL_V1, NEW_STILL, "scenarios: still_item_point logs its reads", optional=True)

src = sub(src,
          "SETTLE_WAIT_MS = 10000.0\n",
          "SETTLE_WAIT_MS = 10000.0\n"
          "STAGE_WAIT_MS = 3000.0    # how long the panel stage may take to arrive after the open\n",
          "scenarios: STAGE_WAIT_MS")

src = sub(src,
          "    def after(self, t_ms, kinds=None):\n"
          "        at = bisect.bisect_left(self.times, t_ms)\n"
          "        return [event for event in self.events[at:] if kinds is None or event.kind in kinds]\n",
          "    def after(self, t_ms, kinds=None):\n"
          "        at = bisect.bisect_left(self.times, t_ms)\n"
          "        return [event for event in self.events[at:] if kinds is None or event.kind in kinds]\n"
          "\n"
          "    def latest(self, proc=\"shell\"):\n"
          "        \"\"\"The newest state sample of `proc` read so far, after reading what arrived; None\n"
          "        when there is none yet.\"\"\"\n"
          "        self.pump()\n"
          "        for event in reversed(self.events):\n"
          "            if event.kind == \"S\" and (event.data or {}).get(\"proc\") == proc:\n"
          "                return event.data\n"
          "        return None\n",
          "scenarios: Timeline.latest")

src = sub(src,
          "def any_open(data):\n",
          "def panel_at_rest(data):\n"
          "    \"\"\"The panel stage holds its panel and reports that it is not transitioning (the 5th\n"
          "    `panel` entry, the SlideLoader's `transitioning`; a probe without it never matches).\"\"\"\n"
          "    panel = data.get(\"panel\") or []\n"
          "    return len(panel) > 4 and bool(panel[0]) and not panel[4]\n"
          "\n"
          "\n"
          "def any_open(data):\n",
          "scenarios: panel_at_rest")

src = sub(src,
          "        if not rect.get(\"found\") or not rect.get(\"shown\"):\n"
          "            return None\n"
          "        return rect[\"x\"], rect[\"y\"]\n"
          "\n"
          "    def nav_point(self, key, scroll_for=True):\n",
          "        if not rect.get(\"found\") or not rect.get(\"shown\"):\n"
          "            return None\n"
          "        return rect[\"x\"], rect[\"y\"]\n"
          "\n"
          "    def still_item_point(self, name, rounds=12, step_ms=150, rest_ms=250):\n"
          "        \"\"\"Output coordinates of a named item of the bar or the overlay once its rect has\n"
          "        stopped moving, or None when it is not on screen or does not come to rest.\n"
          "\n"
          "        The panel stage glides in (SlideLoader): a press at the place a tab is going to be\n"
          "        lands on the backdrop, which closes the panel (`closePanels` 127 ms after the\n"
          "        open, in the first live S1 run), and every later click of that rep went to the\n"
          "        desktop behind a closed panel.\"\"\"\n"
          + NEW_STILL +
          "\n"
          "    def control_open(self):\n"
          "        \"\"\"The newest shell sample says the Control Center is open. Samples come every\n"
          "        40 ms, so this can be that much behind the product.\"\"\"\n"
          "        state = self.timeline.latest(\"shell\") or {}\n"
          "        return bool(state.get(\"controlOpen\") or (state.get(\"panelOpen\") and state.get(\"kind\") == \"control\"))\n"
          "\n"
          "    def nav_point(self, key, scroll_for=True):\n",
          "scenarios: still_item_point + control_open")

OLD_OPEN = (
    "    def open_control(self):\n"
    "        \"\"\"Control Center open with its current page settled; returns the tab ids.\"\"\"\n"
    "        self.ensure_closed()\n"
    "        at = self.tap(*PANELS[\"control\"])\n"
    "        if not self.timeline.wait(is_open(\"control\"), at - 1.0, OPEN_WAIT_MS):\n"
    "            raise Stuck(\"the Control Center did not open\")\n"
    "        state = self.ask(\"shell\")\n"
    "        if not state:\n"
    "            raise Stuck(\"the shell does not answer while the Control Center is open\")\n"
    "        shown = host_of(state, \"cc\").get(\"shown\") or \"\"\n"
    "        self.timeline.wait(sample(\"shell\", host_settled(\"cc\", shown or None)), at - 1.0, SETTLE_WAIT_MS)\n"
    "        tabs = list((state.get(\"cc\") or {}).get(\"tabs\") or [])\n"
    "        if len(tabs) < 2:\n"
    "            raise Skip(f\"the Control Center lists {len(tabs)} tab(s)\")\n"
    "        return tabs\n")
NEW_OPEN = (
    "    def open_control(self):\n"
    "        \"\"\"Control Center open, its stage arrived and its current page settled; returns the\n"
    "        tab ids.\n"
    "\n"
    "        The page host of a retained panel is settled the moment the panel opens, while the\n"
    "        stage itself is still gliding in: `panel[4]` (the loader's `transitioning`) says when\n"
    "        it has arrived. The tab rects are read again after this, one rep at a time.\"\"\"\n"
    "        self.ensure_closed()\n"
    "        at = self.tap(*PANELS[\"control\"])\n"
    "        if not self.timeline.wait(is_open(\"control\"), at - 1.0, OPEN_WAIT_MS):\n"
    "            raise Stuck(\"the Control Center did not open\")\n"
    "        state = self.ask(\"shell\")\n"
    "        if not state:\n"
    "            raise Stuck(\"the shell does not answer while the Control Center is open\")\n"
    "        shown = host_of(state, \"cc\").get(\"shown\") or \"\"\n"
    "        self.timeline.wait(sample(\"shell\", host_settled(\"cc\", shown or None)), at - 1.0, SETTLE_WAIT_MS)\n"
    "        tabs = list((state.get(\"cc\") or {}).get(\"tabs\") or [])\n"
    "        if len(tabs) < 2:\n"
    "            raise Skip(f\"the Control Center lists {len(tabs)} tab(s)\")\n"
    "        if len(state.get(\"panel\") or []) > 4:\n"
    "            self.timeline.wait(sample(\"shell\", panel_at_rest), at - 1.0, STAGE_WAIT_MS)\n"
    "        return tabs\n")
src = sub(src, OLD_OPEN, NEW_OPEN, "scenarios: open_control waits for the stage")

src = sub(src,
          "    entries = []\n"
          "    for tab in order:\n"
          "        at = ctx.click_at(*rects[tab])\n"
          "        entry = {\"tab\": tab, \"t\": round(at, 3)}\n"
          "        entry[\"react_ms\"] = latency(timeline, at, mark(f\"cc.tab {tab}\"), 5000)\n",
          "    entries = []\n"
          "    rec[\"clicks\"] = entries        # the same list: a stop in the middle keeps what was clicked\n"
          "    for tab in order:\n"
          "        at = control_click(ctx, rects[tab], rec)\n"
          "        entry = {\"tab\": tab, \"t\": round(at, 3)}\n"
          "        entry[\"react_ms\"] = latency(timeline, at, mark(f\"cc.tab {tab}\"), 5000)\n"
          "        entry[\"select_ms\"] = latency(timeline, at, mark(f\"cc.select {tab}\"), 5000)\n",
          "scenarios: cc_clicks")

OLD_REACTION = (
    "def reaction_times(timeline, clicks, limit_of):\n"
    "    \"\"\"For each click the time until the shell switched to that tab; None when the next click\n"
    "    (or `limit_of` ms for the last one) came first, or the mark never showed.\"\"\"\n"
    "    out = []\n"
    "    for index, click in enumerate(clicks):\n"
    "        limit = click[\"t\"] + limit_of(index)\n"
    "        hit = timeline.first(click[\"t\"] - 1.0, mark(f\"cc.tab {click['tab']}\"))\n"
    "        out.append(round(hit.epoch - click[\"t\"], 2) if hit and hit.epoch <= limit else None)\n"
    "    return out\n")
NEW_REACTION = (
    "def tab_points(ctx, tabs):\n"
    "    \"\"\"Where the tab buttons are now, read for every rep: the panel was reopened and has to\n"
    "    be at rest before the first click of the rep (see Ctx.still_item_point).\"\"\"\n"
    "    rects = {}\n"
    "    for tab in tabs:\n"
    "        point = ctx.still_item_point(f\"perfTab_{tab}\")\n"
    "        if point is None:\n"
    "            ctx.escape(\"s1: the tab rects cannot be read\")\n"
    "            raise Skip(f\"perfTab_{tab} is not on screen or does not come to rest\")\n"
    "        rects[tab] = point\n"
    "    return rects\n"
    "\n"
    "\n"
    "def control_click(ctx, point, rec):\n"
    "    \"\"\"One click on a tab of the Control Center, and only while the newest sample says the\n"
    "    panel is open. Otherwise the rep ends here, with the clicks it made, and the session with\n"
    "    it: nothing of ours may land on the desktop behind a closed panel.\"\"\"\n"
    "    if not ctx.control_open():\n"
    "        rec[\"stopped\"] = \"the Control Center is not open any more\"\n"
    "        ctx.records.append(rec)\n"
    "        raise Stuck(rec[\"stopped\"])\n"
    "    return ctx.click_at(*point)\n"
    "\n"
    "\n"
    "def reaction_times(timeline, clicks, limit_of, prefix=\"cc.tab\"):\n"
    "    \"\"\"For each click the time until the shell switched to that tab (`cc.tab`), or until the\n"
    "    tab's own handler ran (`cc.select`: the click reached the button); None when the next click\n"
    "    (or `limit_of` ms for the last one) came first, or the mark never showed.\"\"\"\n"
    "    out = []\n"
    "    for index, click in enumerate(clicks):\n"
    "        limit = click[\"t\"] + limit_of(index)\n"
    "        hit = timeline.first(click[\"t\"] - 1.0, mark(f\"{prefix} {click['tab']}\"))\n"
    "        out.append(round(hit.epoch - click[\"t\"], 2) if hit and hit.epoch <= limit else None)\n"
    "    return out\n")
src = sub(src, OLD_REACTION, NEW_REACTION, "scenarios: tab_points, control_click, reaction_times prefix")

OLD_HEAD = (
    "    \"\"\"S1: switching tabs freezes the shell. A rep is one pass, one random walk or one burst.\"\"\"\n"
    "    rng = random.Random(seed)\n"
    "    tabs = ctx.open_control()\n"
    "    rects = {}\n"
    "    for tab in tabs:\n"
    "        point = ctx.item_point(f\"perfTab_{tab}\")\n"
    "        if point is None:\n"
    "            raise Skip(f\"perfTab_{tab} is not on screen\")\n"
    "        rects[tab] = point\n"
    "    timeline = ctx.timeline\n"
    "    ctx.park()\n"
    "    try:\n"
    "        for variant in variants:\n"
    "            for rep in range(reps):\n"
    "                ctx.note(f\"s1 {variant} rep={rep}\")\n")
NEW_HEAD = (
    "    \"\"\"S1: switching tabs freezes the shell. A rep is one pass, one random walk or one burst.\n"
    "\n"
    "    The tab rects are read again at the start of every rep: the panel is reopened between\n"
    "    reps and glides in, a click at a tab's place before it has arrived closes the panel.\"\"\"\n"
    "    rng = random.Random(seed)\n"
    "    tabs = ctx.open_control()\n"
    "    timeline = ctx.timeline\n"
    "    ctx.park()\n"
    "    try:\n"
    "        for variant in variants:\n"
    "            for rep in range(reps):\n"
    "                rects = tab_points(ctx, tabs)\n"
    "                ctx.note(f\"s1 {variant} rep={rep}\")\n")
src = sub(src, OLD_HEAD, NEW_HEAD, "scenarios: s1_control reads the rects per rep")

src = sub(src,
          "                started = ctx.now()\n"
          "                clicks_ = []\n",
          "                started = ctx.now()\n"
          "                clicks_ = []\n"
          "                rec[\"clicks\"] = clicks_      # the same list: a stop in the middle keeps what was clicked\n",
          "scenarios: s1 rep keeps its clicks")
src = sub(src,
          "                            at = ctx.click_at(*rects[current])\n",
          "                            at = control_click(ctx, rects[current], rec)\n",
          "scenarios: random clicks guarded")
src = sub(src,
          "                            at = ctx.click_at(*rects[tab])\n",
          "                            at = control_click(ctx, rects[tab], rec)\n",
          "scenarios: fast clicks guarded")
src = sub(src,
          "                    rec[\"react_ms\"] = reaction_times(timeline, clicks_, lambda index: gaps[index] if index < len(gaps) else 5000.0)\n",
          "                    def limit_of(index):\n"
          "                        return gaps[index] if index < len(gaps) else 5000.0\n"
          "\n"
          "                    rec[\"react_ms\"] = reaction_times(timeline, clicks_, limit_of)\n"
          "                    rec[\"select_ms\"] = reaction_times(timeline, clicks_, limit_of, \"cc.select\")\n",
          "scenarios: select_ms for random/fast")

src = sub(src,
          "                    ctx.meta[\"truncated\"] = f\"s1 {variant} after rep {rep}\"\n"
          "                    return\n"
          "                ctx.open_control()\n"
          "    finally:\n"
          "        ctx.park()\n",
          "                    ctx.meta[\"truncated\"] = f\"s1 {variant} after rep {rep}\"\n"
          "                    return\n"
          "                if rep < reps - 1 or variant != variants[-1]:\n"
          "                    ctx.open_control()          # the next rep starts over; the last one leaves nothing open\n"
          "    finally:\n"
          "        ctx.park()\n",
          "scenarios: no reopen after the last rep")

OLD_WS = (
    "def workspace_round(ctx):\n"
    "    \"\"\"To the next workspace and back, through niri's own binds (Mod+<index>).\"\"\"\n"
    "    rec = {}\n"
    "    before = ctx.probe.focused_workspace()\n"
    "    rec[\"before\"] = before\n"
    "    idx = (before or {}).get(\"idx\")\n"
    "    if not idx:\n"
    "        rec[\"skipped\"] = \"niri does not say which workspace is focused\"\n"
    "        return rec\n"
    "    other = idx + 1 if idx < 9 else idx - 1\n"
    "    if other < 1:\n"
    "        rec[\"skipped\"] = \"no other workspace index\"\n"
    "        return rec\n"
    "    ctx.tap(\"super\", str(other))\n"
    "    ctx.sleep(700)\n"
    "    rec[\"away\"] = ctx.probe.focused_workspace()\n"
    "    ctx.tap(\"super\", str(idx))\n"
    "    ctx.sleep(700)\n"
    "    rec[\"after\"] = ctx.probe.focused_workspace()\n"
    "    rec[\"restored\"] = (rec[\"after\"] or {}).get(\"idx\") == idx\n"
    "    if not rec[\"restored\"]:\n"
    "        ctx.tap(\"super\", str(idx))\n"
    "        ctx.sleep(700)\n"
    "        rec[\"after_retry\"] = ctx.probe.focused_workspace()\n"
    "    return rec\n")
NEW_WS = (
    "def workspace_round(ctx):\n"
    "    \"\"\"To another workspace and back, through niri's own binds (Mod+<index>).\n"
    "\n"
    "    niri drops an empty workspace the moment it loses the focus, so the round only leaves a\n"
    "    workspace that holds a window. From an empty one it traded the owner's workspace for a\n"
    "    new one at the same index (live, 2026-11-27: id 4 became id 5). `restored` compares\n"
    "    the ids: the same index can be another workspace.\"\"\"\n"
    "    rec = {}\n"
    "    before = ctx.probe.focused_workspace()\n"
    "    rec[\"before\"] = before\n"
    "    idx = (before or {}).get(\"idx\")\n"
    "    if not idx:\n"
    "        rec[\"skipped\"] = \"niri does not say which workspace is focused\"\n"
    "        return rec\n"
    "    try:\n"
    "        windows = ctx.probe.workspace_windows()\n"
    "    except ProbeError as error:\n"
    "        rec[\"skipped\"] = \"niri does not list the windows\"\n"
    "        ctx.problems.append({\"t\": round(ctx.now(), 3), \"probe\": \"windows\", \"error\": str(error)[:240]})\n"
    "        return rec\n"
    "    if before.get(\"id\") not in windows:\n"
    "        rec[\"skipped\"] = \"the focused workspace holds no window: leaving it would remove it\"\n"
    "        return rec\n"
    "    other = idx + 1 if idx < 9 else idx - 1\n"
    "    if other < 1:\n"
    "        rec[\"skipped\"] = \"no other workspace index\"\n"
    "        return rec\n"
    "    ctx.tap(\"super\", str(other))\n"
    "    ctx.sleep(700)\n"
    "    rec[\"away\"] = ctx.probe.focused_workspace()\n"
    "    ctx.tap(\"super\", str(idx))\n"
    "    ctx.sleep(700)\n"
    "    rec[\"after\"] = ctx.probe.focused_workspace()\n"
    "    rec[\"restored\"] = (rec[\"after\"] or {}).get(\"id\") == before.get(\"id\")\n"
    "    if not rec[\"restored\"]:\n"
    "        ctx.tap(\"super\", str(idx))\n"
    "        ctx.sleep(700)\n"
    "        rec[\"after_retry\"] = ctx.probe.focused_workspace()\n"
    "        if (rec[\"after_retry\"] or {}).get(\"id\") != before.get(\"id\"):\n"
    "            ctx.problems.append({\"t\": round(ctx.now(), 3), \"workspace\": \"not restored\",\n"
    "                                 \"before\": before, \"last\": rec[\"after_retry\"]})\n"
    "    return rec\n")
src = sub(src, OLD_WS, NEW_WS, "scenarios: safe workspace round")

ast.parse(src)
open("scenarios.py", "w").write(src)

# ---- probe.py: which workspaces hold a window ---------------------------------------------
src = open("probe.py").read()
src = sub(src,
          "        for space in niri([\"workspaces\"], self.env):\n"
          "            if space.get(\"is_focused\"):\n"
          "                return {\"id\": space.get(\"id\"), \"idx\": space.get(\"idx\")}\n"
          "        return {}\n",
          "        for space in niri([\"workspaces\"], self.env):\n"
          "            if space.get(\"is_focused\"):\n"
          "                return {\"id\": space.get(\"id\"), \"idx\": space.get(\"idx\")}\n"
          "        return {}\n"
          "\n"
          "    def workspace_windows(self) -> list:\n"
          "        \"\"\"Ids of the workspaces that hold at least one window, as niri lists them.\"\"\"\n"
          "        return sorted({window.get(\"workspace_id\") for window in niri([\"windows\"], self.env)\n"
          "                       if window.get(\"workspace_id\") is not None})\n",
          "probe: workspace_windows")
ast.parse(src)
open("probe.py", "w").write(src)

# ---- sim.py: the model answers the new probe call -----------------------------------------
src = open("sim.py").read()
src = sub(src,
          "    def focused_workspace(self):\n"
          "        return {\"id\": self.workspace, \"idx\": self.workspace}\n",
          "    def focused_workspace(self):\n"
          "        return {\"id\": self.workspace, \"idx\": self.workspace}\n"
          "\n"
          "    def workspace_windows(self):\n"
          "        return [self.workspace]        # the focused workspace holds a window: the round may leave it\n",
          "sim: SimShell.workspace_windows")
src = sub(src,
          "    def focused_workspace(self):\n"
          "        return self.sim.focused_workspace()\n",
          "    def focused_workspace(self):\n"
          "        return self.sim.focused_workspace()\n"
          "\n"
          "    def workspace_windows(self):\n"
          "        return self.sim.workspace_windows()\n",
          "sim: FakeProbe.workspace_windows")
ast.parse(src)
open("sim.py", "w").write(src)

# ---- probe/Probe.qml: the stage's `transitioning` in the state sample ----------------------
src = open("probe/Probe.qml").read()
src = sub(src,
          "            if (loader) o.panel = [loader.item ? 1 : 0, loader.shown, loader.dormant, loader.warmupActive];\n",
          "            if (loader) o.panel = [loader.item ? 1 : 0, loader.shown, loader.dormant, loader.warmupActive, loader.transitioning];\n",
          "Probe.qml: panel[4] = transitioning")
src = sub(src,
          "        // methods exist in the metaobject but calling them throws. A real Item (most of\n"
          "        // the shell's own items) maps exactly; anything else falls back to adding the\n"
          "        // readable x/y up the parent chain - exact for the untransformed trees the\n"
          "        // harness clicks (Settings sidebar, CC tabs).\n"
          "        try {\n"
          "            return item.mapToScene(Qt.point(item.width / 2, item.height / 2));\n"
          "        } catch (error) {\n"
          "            let x = item.width / 2, y = item.height / 2, node = item, guard = 0;\n",
          "        // methods exist in the metaobject but calling them throws. A real Item (most of\n"
          "        // the shell's own items) maps exactly; a Control maps through a part that fills\n"
          "        // it, which keeps the transforms of its parents (the panel stage glides in by\n"
          "        // translating its content: the x/y of a tab never change). Anything else falls\n"
          "        // back to adding the readable x/y up the parent chain - exact only where nothing\n"
          "        // transforms the tree (the Settings sidebar).\n"
          "        try {\n"
          "            return item.mapToScene(Qt.point(item.width / 2, item.height / 2));\n"
          "        } catch (error) {\n"
          "            for (const part of [item.background, item.contentItem]) {\n"
          "                try {\n"
          "                    if (part && Math.abs(part.width - item.width) < 1 && Math.abs(part.height - item.height) < 1)\n"
          "                        return part.mapToScene(Qt.point(part.width / 2, part.height / 2));\n"
          "                } catch (ignored) {}\n"
          "            }\n"
          "            let x = item.width / 2, y = item.height / 2, node = item, guard = 0;\n",
          "Probe.qml: a Control maps through its background")
open("probe/Probe.qml", "w").write(src)

# ---- probe_patch.py: the cc.tab mark names the tab that was ENTERED ------------------------
src = open("probe_patch.py").read()
src = sub(src,
          "edit(\"qml/panels/ControlCenter.qml\",\n"
          "     \"    onCurrentTabChanged: { editing = false; ShellState.controlTab = currentTab; markTabRead(); refreshControls(); }\\n\",\n",
          "# `selectedTab` is a binding on currentTab; read inside the change handler it still names\n"
          "# the tab the panel is LEAVING (the first live S1 run saw every mark one tab behind), so\n"
          "# the mark reads the registry with the new index itself.\n"
          "edit(\"qml/panels/ControlCenter.qml\",\n"
          "     \"    onCurrentTabChanged: { editing = false; ShellState.controlTab = currentTab; markTabRead(); refreshControls(); }\\n\",\n",
          "probe_patch: comment")
src = sub(src,
          "Probe.mark(\"cc.tab \" + (root.selectedTab ? root.selectedTab.id : \"?\"));",
          "Probe.mark(\"cc.tab \" + (ControlRegistry.tabForIndex(currentTab).id || \"?\"));",
          "probe_patch: cc.tab reads the entered tab")
ast.parse(src)
open("probe_patch.py", "w").write(src)

print("edits applied:" if CHANGED else "nothing to do (already patched)")
for note in CHANGED:
    print("  -", note)
