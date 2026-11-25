#!/usr/bin/env python3
"""Agent-2: instrument a SCRATCH COPY of the Settings sources for the stutter probe (round 2).

Runs on the host:  python3 -I probe_patch2.py --src /tmp/lme-probe2/src-fixed [--dry]

Round 2 differs from probe_patch.py: no FrameAnimation heartbeat (it forced frames and
inflated the first-page latency); real rendered frames are counted through the window's
frameSwapped signal; the script can hide/show the window (Probe.reopenRequested()); the
accept() tail is split further. The same patch applies to the stock tree and to the fixed
tree: edits tagged "stock" or "fixed" are applied only when PageHost.qml has (or has not)
`asyncPages`; an edit for the wrong variant is skipped, never guessed.

Never point --src at a real clone: the patch rewrites files in place. The script refuses a
tree that contains a .git directory. Every edit anchors on exact source text that must occur
exactly once, so a drifted file fails loudly instead of silently producing an uninstrumented run.

What gets logged (stderr of quickshell, prefix "@@PROBE"):
  m  phase marker            s  state transition (only on change)   F  rendered frame (frameSwapped)
  g  GUI-thread stall (4 ms timer gap)                             b  page build: resolve ms + synchronous build ms
  l  page loaded             k  prewarm tick (left, gated)         a  ShellState.accept(): parse / identity / assign / snapshot / tail
  r  ShellState.run() call   q  request written to the backend     x  request blocked by LME_PROBE_NOPOLL
"""
import argparse
import py_compile
import sys
from pathlib import Path

PROBE_QML = r'''// Probe.qml — Agent-2 stutter probe, SCRATCH COPY ONLY. GUI-thread timeline logger.
pragma Singleton
import QtQuick
import Quickshell

QtObject {
    id: root
    property bool hiRes: typeof performance !== "undefined" && typeof performance.now === "function"
    readonly property bool noPrewarm: Quickshell.env("LME_PROBE_NOPREWARM") === "1"
    readonly property bool noPoll: Quickshell.env("LME_PROBE_NOPOLL") === "1"
    readonly property string script: Quickshell.env("LME_PROBE_SCRIPT") || "use"
    readonly property int runMs: Number(Quickshell.env("LME_PROBE_RUNTIME_MS") || 21000)
    readonly property var pollActions: ["displayRefresh", "idleRefresh", "nightLightRefresh", "platformRefresh", "keybindRefresh"]
    property real started: 0
    property real lastTimer: 0
    property int frames: 0
    property int acceptCount: 0
    property var sections: ({})
    signal reopenRequested()

    function now() { return hiRes ? performance.now() : Date.now(); }
    function rel(t) { return (t - started).toFixed(hiRes ? 2 : 0); }
    // console.log is filtered out of stderr by quickshell's default rules; warnings are not.
    function out(line) { console.warn("@@PROBE " + line); }
    function mark(name, extra) { out("m " + rel(now()) + " " + name + (extra ? " " + extra : "")); }
    function state(key, value) {
        if (sections[key] === value) return;
        sections[key] = value;
        out("s " + rel(now()) + " " + key + "=" + value);
    }
    function frame() { frames++; out("F " + rel(now())); }
    function timerBeat() {
        const t = now();
        if (lastTimer && t - lastTimer >= 9.5) out("g " + rel(lastTimer) + " " + (t - lastTimer).toFixed(2));
        lastTimer = t;
    }
    function built(key, t0, t1, t2, async) {
        out("b " + rel(t0) + " " + key + " resolve=" + (t1 - t0).toFixed(2) + " build=" + (t2 - t1).toFixed(2) + " async=" + async);
    }
    function pageLoaded(key, t) { out("l " + rel(t) + " " + key); }
    function tree(key, item) {
        const t = now();
        const n = count(item);
        out("t " + rel(t) + " " + key + " items=" + n + " count=" + (now() - t).toFixed(2));
    }
    function count(item) {
        if (!item) return 0;
        let n = 1;
        const kids = item.data;
        if (!kids) return n;
        for (let i = 0; i < kids.length; i++) n += count(kids[i]);
        return n;
    }
    function tick(t, left, gated) { out("k " + rel(t) + " left=" + left + " gated=" + gated); }
    function runCalled(action) { out("r " + rel(now()) + " " + action); }
    function sent(action) { out("q " + rel(now()) + " " + action); }
    function blocked(action) { out("x " + rel(now()) + " " + action); }
    function accepted(t0, t1, t2, t3, t4, t5, bytes, next) {
        acceptCount++;
        let sizes = "";
        if (acceptCount === 1 || acceptCount % 50 === 0) {
            const list = [];
            for (const key in next) list.push([key, JSON.stringify(next[key]).length]);
            list.sort((a, b) => b[1] - a[1]);
            sizes = " sections=" + list.map(pair => pair[0] + ":" + pair[1]).join(",");
        }
        out("a " + rel(t0) + " parse=" + (t1 - t0).toFixed(2) + " identity=" + (t2 - t1).toFixed(2)
            + " assign=" + (t3 - t2).toFixed(2) + " snapshot=" + (t4 - t3).toFixed(2) + " tail=" + (t5 - t4).toFixed(2)
            + " bytes=" + bytes + " action=" + ((next.lastResult || {}).action || "") + sizes);
    }
    function quit() { mark("quit"); Qt.quit(); }
    Component.onCompleted: {
        started = now();
        out("start epoch=" + Date.now() + " mono=" + started + " hires=" + hiRes
            + " noprewarm=" + noPrewarm + " nopoll=" + noPoll + " script=" + script + " runMs=" + runMs);
    }
}
'''

PROBE_VIEW = r'''    // ---- Agent-2 probe (scratch copy only): scripted use of the app, timed from the first page load ----
    property bool probeStarted: false
    property real probeT0: 0
    Component.onCompleted: Probe.mark("view.completed", "pages=" + SettingsRegistry.pages.length)
    function probeScroll(fraction, ms, tag) {
        const t = Probe.now();
        const max = Math.max(0, pageScroll.contentHeight - pageScroll.height);
        const to = Math.round(max * fraction);
        probeAnim.stop(); probeAnim.duration = ms; probeAnim.to = to; probeAnim.restart();
        Probe.mark("script." + tag, "contentY->" + to + "/" + max + " call=" + (Probe.now() - t).toFixed(2));
    }
    function probeNav(key, tag) {
        const t = Probe.now();
        root.navigate(key);
        Probe.mark("script." + tag, "->" + key + " call=" + (Probe.now() - t).toFixed(2));
    }
    function probeType(text, tag) {
        const t = Probe.now();
        search.text = text;
        Probe.mark("script." + tag, "search=" + text + " call=" + (Probe.now() - t).toFixed(2));
    }
    function probeHide(tag) {
        const t = Probe.now();
        root.closeRequested();
        Probe.mark("script." + tag, "call=" + (Probe.now() - t).toFixed(2));
    }
    function probeShow(tag) {
        const t = Probe.now();
        Probe.reopenRequested();
        Probe.mark("script." + tag, "call=" + (Probe.now() - t).toFixed(2));
    }
    // Idle 2.5 s, scroll down 1.2 s, scroll up 1.2 s, repeated: builds that start in an idle
    // gap are still in flight when the next scroll begins.
    function probeMixed() {
        const plan = [];
        let at = 2500, n = 0;
        while (at < Probe.runMs - 3000) {
            const tag = "" + (++n);
            plan.push({at: at, go: function() { root.probeScroll(0.8, 1200, "mdown" + tag); }});
            plan.push({at: at + 1200, go: function() { root.probeScroll(0, 1200, "mup" + tag); }});
            at += 4900;
        }
        return plan;
    }
    readonly property var probePlan: Probe.script === "idle" ? [
        {at: 22000, go: function() { root.probeHide("hide1"); }},
        {at: 24000, go: function() { root.probeShow("show1"); }}
    ] : Probe.script === "mixed" ? root.probeMixed() : Probe.script === "cold" ? [
        {at: 900, go: function() { root.probeNav("wallpaper", "cold1"); }},
        {at: 2600, go: function() { root.probeNav("display", "cold2"); }},
        {at: 3800, go: function() { root.probeScroll(0.8, 800, "scroll1"); }},
        {at: 5000, go: function() { root.probeScroll(0, 600, "scroll2"); }},
        {at: 6200, go: function() { root.probeNav("appearance", "cold3"); }},
        {at: 7400, go: function() { root.probeScroll(0.8, 800, "scroll3"); }},
        {at: 8600, go: function() { root.probeScroll(0, 600, "scroll4"); }}
    ] : [
        {at: 1000, go: function() { root.probeScroll(0.8, 800, "scroll1"); }},
        {at: 2400, go: function() { root.probeScroll(0, 600, "scroll2"); }},
        {at: 3600, go: function() { root.probeNav("display", "nav1"); }},
        {at: 4600, go: function() { root.probeScroll(0.8, 800, "scroll3"); }},
        {at: 6000, go: function() { root.probeScroll(0, 600, "scroll4"); }},
        {at: 7200, go: function() { root.probeNav("keybinds", "nav2"); }},
        {at: 8200, go: function() { root.probeScroll(0.8, 800, "scroll5"); }},
        {at: 9600, go: function() { root.probeScroll(0, 600, "scroll6"); }},
        {at: 10800, go: function() { root.probeNav("topbar", "nav3"); }},
        {at: 11800, go: function() { root.probeScroll(0.8, 800, "scroll7"); }},
        {at: 13200, go: function() { root.probeScroll(0, 600, "scroll8"); }},
        {at: 14400, go: function() { root.probeNav("wallpaper", "nav4"); }},
        {at: 15400, go: function() { root.probeScroll(0.8, 800, "scroll9"); }},
        {at: 16800, go: function() { root.probeScroll(0, 600, "scroll10"); }},
        {at: 17800, go: function() { root.probeNav("appearance", "nav5"); }},
        {at: 18400, go: function() { root.probeType("w", "type1"); }},
        {at: 18520, go: function() { root.probeType("wa", "type2"); }},
        {at: 18640, go: function() { root.probeType("wal", "type3"); }},
        {at: 18760, go: function() { root.probeType("wall", "type4"); }},
        {at: 19500, go: function() { root.probeType("", "type5"); }},
        {at: 20500, go: function() { root.probeHide("hide1"); }},
        {at: 22500, go: function() { root.probeShow("show1"); }},
        {at: 24500, go: function() { root.probeScroll(0.8, 800, "scroll11"); }},
        {at: 25500, go: function() { root.probeScroll(0, 600, "scroll12"); }},
        {at: 27500, go: function() { root.probeHide("hide2"); }},
        {at: 29500, go: function() { root.probeShow("show2"); }},
        {at: 31000, go: function() { root.probeNav("display", "nav6"); }}
    ]
    NumberAnimation { id: probeAnim; target: pageScroll; property: "contentY"; duration: 800; easing.type: Easing.InOutQuad }
    Timer {
        id: probeScript
        interval: 25; repeat: true
        property int step: 0
        onTriggered: {
            const elapsed = Probe.now() - root.probeT0;
            while (step < root.probePlan.length && root.probePlan[step].at <= elapsed) {
                const item = root.probePlan[step++];
                try { item.go(); } catch (error) { Probe.mark("script.error", String(error)); }
            }
            if (step >= root.probePlan.length) stop();
        }
    }
    Timer {
        id: probeQuit
        interval: 50; repeat: true; running: root.probeStarted
        onTriggered: if (Probe.now() - root.probeT0 >= Probe.runMs) { stop(); Probe.quit(); }
    }
'''

PROBE_VIEW_FIXED = r'''    property int probeActivity: 0
    onLastActivityChanged: probeActivity++
    // v3 carries framesRendered (production frame counter); sample it, do not redefine its
    // handler, and leave frame lines to the window-level counter in SettingsApplication.
    Timer {
        interval: 100; repeat: true; running: true
        property int seen: 0
        property int seenFrames: 0
        onTriggered: {
            if (root.probeActivity !== seen) { seen = root.probeActivity; Probe.state("activity", String(seen)); }
            Probe.state("framesRendered", String(root.framesRendered))
            while (seenFrames < root.framesRendered) { seenFrames++; Probe.frame(); }
        }
    }
'''

PROBE_APP = r'''    Component.onCompleted: Probe.mark("app.completed")
    Connections {
        target: Probe
        function onReopenRequested() { root.shown = true; linger.stop(); }
    }
    Timer {
        interval: 4; repeat: true; running: true
        onTriggered: Probe.timerBeat()
    }
    Timer {
        interval: 50; repeat: true; running: true
        onTriggered: {
            Probe.state("featureCatalog.ready", String(FeatureCatalog.ready));
            Probe.state("theme.ready", String(Theme.ready));
            Probe.state("backendReady", String(ShellState.backendReady));
            Probe.state("catalog.pages", String(SettingsRegistry.pages.length));
        }
    }
'''

PROBE_WINDOW = r'''        onVisibleChanged: Probe.mark("window.visible", String(visible))
'''

PROBE_LOG_PY = '''

def probe_cmd(message: str) -> None:
    """Agent-2 probe (scratch copy only): append subprocess/emission events to a log file."""
    path = os.environ.get("LME_PROBE_CMDLOG")
    if not path: return
    with open(path, "a") as handle:
        handle.write(f"{time.monotonic():.3f} {os.getpid()} {message}\\n")
'''

ENTRY_HEAD = (
    "        let page = entries[pageKey];\n"
    "        if (page) { touch(pageKey); return page; }\n"
)
TIMER_GATE_STOCK = "            if (root.prewarmGate && !root.prewarmGate()) return;\n"
TIMER_GATE_FIXED = "            if (!root.active) return; // a hidden window shows nothing new by building\n            if (root.prewarmGate && !root.prewarmGate()) return;\n"
PREWARM_QUEUE = "        prewarmQueue = source ? source() : [];\n    }\n"
PRESENT = "    function present(page) {\n"
LOADED = "            onLoaded: {\n                root.pageLoaded(item);\n"
STATUS_ANCHOR = "            if (status === Loader.Loading) return;\n"

# (variant, relative path, exact anchor, replacement); variant "both" always applies
EDITS = [
    ("both", "settings.qml",
     "//@ pragma AppId lme-shell-settings\n",
     "//@ pragma AppId lme-shell-settings-probe\n"),

    ("both", "qml/services/qmldir",
     "singleton FrameLogger 1.0 FrameLogger.qml\n",
     "singleton FrameLogger 1.0 FrameLogger.qml\nsingleton Probe 1.0 Probe.qml\n"),

    ("both", "qml/services/ShellState.qml",
     "    function run(action, payload) {\n",
     "    function run(action, payload) {\n        Probe.runCalled(action);\n"),
    ("both", "qml/services/ShellState.qml",
     "    function send(action, payload) { // REL: scripts/desktop_backend.py::handle – sends {action,...} over stdin.\n"
     "        if (!backend.running || !backendReady) {\n",
     "    function send(action, payload) { // REL: scripts/desktop_backend.py::handle – sends {action,...} over stdin.\n"
     "        if (Probe.noPoll && Probe.pollActions.indexOf(action) >= 0) { Probe.blocked(action); return; }\n"
     "        if (!backend.running || !backendReady) {\n"),
    ("both", "qml/services/ShellState.qml",
     '        backend.write(JSON.stringify(request) + "\\n"); // Protocol: JSON-lines request; result carries ok/action/message/sequence/pending.\n',
     '        backend.write(JSON.stringify(request) + "\\n"); // Protocol: JSON-lines request; result carries ok/action/message/sequence/pending.\n'
     "        Probe.sent(action);\n"),
    ("both", "qml/services/ShellState.qml",
     "    function accept(data) {\n"
     "        try {\n"
     "            const next = JSON.parse(data);\n",
     "    function accept(data) {\n"
     "        try {\n"
     "            const probeT0 = Probe.now();\n"
     "            const next = JSON.parse(data);\n"
     "            const probeT1 = Probe.now();\n"),
    ("both", "qml/services/ShellState.qml",
     "            pendingActions = ownership.state.pending;\n"
     "            const oldBrightness = system.brightness;\n",
     "            pendingActions = ownership.state.pending;\n"
     "            const probeT2 = Probe.now();\n"
     "            const oldBrightness = system.brightness;\n"),
    ("both", "qml/services/ShellState.qml",
     "            snapshot = next;\n"
     "            if (!demo && !settingsApp && !backendDemo) NativeState.compareSections(",
     "            const probeT3 = Probe.now();\n"
     "            snapshot = next;\n"
     "            if (!demo && !settingsApp && !backendDemo) NativeState.compareSections("),
    ("both", "qml/services/ShellState.qml",
     "            FeatureCatalog.validate(next.catalogValidation);\n"
     "            const wasReady = backendReady;\n",
     "            FeatureCatalog.validate(next.catalogValidation);\n"
     "            const probeT4 = Probe.now();\n"
     "            const wasReady = backendReady;\n"),
    ("both", "qml/services/ShellState.qml",
     '        } catch (error) { console.warn("Invalid desktop backend message:", error); }\n',
     "            Probe.accepted(probeT0, probeT1, probeT2, probeT3, probeT4, Probe.now(), data.length, next);\n"
     '        } catch (error) { console.warn("Invalid desktop backend message:", error); }\n'),

    ("both", "qml/components/PageHost.qml",
     'import "../theme"\n',
     'import "../theme"\nimport "../services"\n'),
    ("both", "qml/components/PageHost.qml",
     ENTRY_HEAD,
     ENTRY_HEAD + "        const probeT0 = Probe.now();\n"),
    ("both", "qml/components/PageHost.qml",
     "        if (!content) return null;\n",
     "        if (!content) return null;\n        const probeT1 = Probe.now();\n"),
    ("both", "qml/components/PageHost.qml",
     "        page.sourceComponent = content;\n"
     "        trim();\n"
     "        return page;\n",
     "        page.sourceComponent = content;\n"
     "        trim();\n"
     "        Probe.built(pageKey, probeT0, probeT1, Probe.now(), page.asynchronous);\n"
     "        Probe.tree(pageKey, page.asynchronous ? null : page.item);\n"
     "        return page;\n"),
    ("stock", "qml/components/PageHost.qml",
     TIMER_GATE_STOCK,
     "            const probeGate = root.prewarmGate ? !root.prewarmGate() : false;\n"
     "            Probe.tick(Probe.now(), root.prewarmQueue.length, probeGate);\n"
     "            if (probeGate) return;\n"),
    ("fixed", "qml/components/PageHost.qml",
     TIMER_GATE_FIXED,
     "            const probeGate = !root.active || (root.prewarmGate && !root.prewarmGate());\n"
     "            Probe.tick(Probe.now(), root.prewarmQueue.length, probeGate);\n"
     "            if (probeGate) return;\n"),
    ("both", "qml/components/PageHost.qml",
     PREWARM_QUEUE,
     "        prewarmQueue = source ? source() : [];\n"
     '        Probe.mark("prewarm.armed", "count=" + prewarmQueue.length + " skip=" + Probe.noPrewarm);\n'
     "        if (Probe.noPrewarm) prewarmQueue = [];\n"
     "    }\n"),
    ("both", "qml/components/PageHost.qml",
     PRESENT,
     PRESENT + '        Probe.mark("present", page.pageKey + " animate=" + (animate && Theme.animations));\n'),
    ("both", "qml/components/PageHost.qml",
     LOADED,
     "            onLoaded: {\n"
     "                Probe.pageLoaded(pageKey, Probe.now());\n"
     "                root.pageLoaded(item);\n"
     "                if (pageKey === root.key) root.present(page);\n"
     "                if (page.asynchronous) Probe.tree(pageKey, item);\n"),
    ("both", "qml/components/PageHost.qml",
     "    onKeyChanged: show()\n",
     "    onKeyChanged: { Probe.mark(\"request\", key); show(); }\n"),
    ("fixed", "qml/components/PageHost.qml",
     STATUS_ANCHOR,
     STATUS_ANCHOR + '                Probe.mark("page.status", pageKey + " " + status + (root.pending === page ? " pending" : ""));\n'),
    ("fixed", "qml/components/PageHost.qml",
     "        delete entries[page.pageKey];\n",
     '        Probe.mark("drop", page.pageKey + (prewarming === page ? " background" : " request"));\n'
     "        delete entries[page.pageKey];\n"),

    ("both", "qml/settings/SettingsView.qml",
     "    property real now: Date.now()\n",
     "    property real now: Date.now()\n" + PROBE_VIEW),
    ("fixed", "qml/settings/SettingsView.qml",
     "    property real lastActivity: 0\n",
     "    property real lastActivity: 0\n" + PROBE_VIEW_FIXED),
    ("both", "qml/settings/SettingsView.qml",
     "                    onPageLoaded: {\n",
     "                    onPageLoaded: {\n"
     "                        if (!probeStarted) { probeStarted = true; probeT0 = Probe.now(); Probe.mark(\"t0.firstpage\"); probeScript.restart(); }\n"
     "                        if (!pagesWarmupArmed) return;"),

    ("both", "qml/settings/SettingsApplication.qml",
     "    property bool startupFailed: false\n",
     "    property bool startupFailed: false\n" + PROBE_APP),
    ("both", "qml/settings/SettingsApplication.qml",
     "    onPreparedChanged: if (prepared) { requestedPage = SettingsRegistry.page(requestedPage).key; initialized = true; }\n",
     "    onPreparedChanged: {\n"
     '        Probe.mark("prepared", String(prepared));\n'
     "        if (prepared) { requestedPage = SettingsRegistry.page(requestedPage).key; initialized = true; }\n"
     "    }\n"),
    ("both", "qml/settings/SettingsApplication.qml",
     '        color: "transparent"\n',
     '        color: "transparent"\n' + PROBE_WINDOW),
    ("both", "qml/settings/SettingsApplication.qml",
     "            active: root.initialized\n",
     "            active: root.initialized\n"
     '            onStatusChanged: Probe.mark("view.status", String(status))\n'),

    ("both", "scripts/command_runner.py",
     "from command_output import DEFAULT_LIMIT, LIMITS, capture, text\n",
     "from command_output import DEFAULT_LIMIT, LIMITS, capture, text\n" + PROBE_LOG_PY),
    ("both", "scripts/command_runner.py",
     "            argv = [sys.executable, str(Path(__file__).with_name('managed_command.py')), '--parent', str(os.getpid()), '--', *argv]\n",
     "            argv = [sys.executable, str(Path(__file__).with_name('managed_command.py')), '--parent', str(os.getpid()), '--', *argv]\n"
     "        probe_t0 = time.monotonic(); probe_cmd(f\"start {name} {' '.join(map(str, args))[:140]}\")\n"),
    ("both", "scripts/command_runner.py",
     '        return (stdout or "").strip()\n',
     '        probe_cmd(f"end {name} {(time.monotonic() - probe_t0) * 1000:.1f}ms")\n'
     '        return (stdout or "").strip()\n'),
    ("both", "scripts/command_runner.py",
     "    def spawn(self, argv: list[str]) -> None:\n"
     "        try:\n",
     "    def spawn(self, argv: list[str]) -> None:\n"
     '        probe_cmd(f"spawn {\' \'.join(argv)[:140]}")\n'
     "        try:\n"),

    ("both", "scripts/desktop_backend.py",
     "from command_runner import CommandError, CommandRunner, TOOLS\n",
     "from command_runner import CommandError, CommandRunner, TOOLS, probe_cmd\n"),
    ("both", "scripts/desktop_backend.py",
     "def emit(backend: DesktopBackend) -> None:  # publishes snapshot+actionPending/lastResult via action_pending.py\n"
     "    publish(backend, FEATURE_CATALOG_ERROR)\n",
     "def emit(backend: DesktopBackend) -> None:  # publishes snapshot+actionPending/lastResult via action_pending.py\n"
     "    probe_t0 = time.monotonic()\n"
     "    publish(backend, FEATURE_CATALOG_ERROR)\n"
     '    probe_cmd(f"emit {(time.monotonic() - probe_t0) * 1000:.1f}ms")\n'),
    ("both", "scripts/desktop_backend.py",
     '                    selector.register(event_process.stdout, selectors.EVENT_READ, "niri"); backend.niri_cache.connect()\n',
     '                    probe_cmd("niri-event-stream spawn")\n'
     '                    selector.register(event_process.stdout, selectors.EVENT_READ, "niri"); backend.niri_cache.connect()\n'),
    ("both", "scripts/desktop_backend.py",
     "        nonlocal event_process\n"
     "        backend.niri_cache.close()\n",
     "        nonlocal event_process\n"
     '        if event_process is not None: probe_cmd("niri-event-stream close")\n'
     "        backend.niri_cache.close()\n"),
    ("both", "scripts/desktop_backend.py",
     "                    error = handle_line(backend.handle, line)   # REL: scripts/action_pending.py::handle_line – stdin JSON-lines\n",
     "                    probe_t0 = time.monotonic()\n"
     "                    error = handle_line(backend.handle, line)   # REL: scripts/action_pending.py::handle_line – stdin JSON-lines\n"
     '                    probe_cmd(f"action {line[:90]!r} {(time.monotonic() - probe_t0) * 1000:.1f}ms")\n'),
]

NEW_FILES = {"qml/services/Probe.qml": PROBE_QML}


def detect_variant(src: Path) -> str:
    text = (src / "qml/components/PageHost.qml").read_text(encoding="utf-8")
    if "property bool asyncPages" in text:
        return "fixed"
    if "property bool firstAsync" in text:
        return "stock"
    sys.exit(f"REFUSED: {src}/qml/components/PageHost.qml is neither the stock nor the fixed file")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--src", required=True, help="scratch tree to instrument (never a real clone)")
    parser.add_argument("--expect", choices=("stock", "fixed"), help="fail if the tree is the other variant")
    parser.add_argument("--dry", action="store_true", help="check anchors only, write nothing")
    args = parser.parse_args()
    src = Path(args.src).resolve()
    if (src / ".git").exists():
        print(f"REFUSED: {src} is a git clone; the probe only patches a scratch copy")
        return 2
    if not (src / "settings.qml").exists():
        print(f"REFUSED: {src} has no settings.qml")
        return 2
    variant = detect_variant(src)
    if args.expect and variant != args.expect:
        print(f"REFUSED: tree is '{variant}', expected '{args.expect}'")
        return 2
    print(f"variant: {variant}")

    files: dict[str, str] = {}
    failed = skipped = 0
    for which, rel, old, new in EDITS:
        if which != "both" and which != variant:
            skipped += 1
            continue
        text = files.get(rel)
        if text is None:
            path = src / rel
            if not path.exists():
                print(f"MISSING FILE {rel}")
                failed += 1
                continue
            text = path.read_text(encoding="utf-8")
        hits = text.count(old)
        if hits != 1:
            print(f"ANCHOR x{hits} (need exactly 1) in {rel}: {old[:70]!r}")
            failed += 1
            continue
        files[rel] = text.replace(old, new)
    if failed:
        print(f"{failed} problem(s); nothing written")
        return 1
    print(f"anchors ok: {sum(1 for e in EDITS if e[0] in ('both', variant))} applied, {skipped} skipped (other variant)")
    if args.dry:
        for rel in files:
            print(f"ok   {rel}")
        print("dry run: nothing written")
        return 0
    for rel, text in files.items():
        (src / rel).write_text(text, encoding="utf-8")
    for rel, text in NEW_FILES.items():
        (src / rel).write_text(text, encoding="utf-8")
    for rel in files:
        if rel.endswith(".py"):
            py_compile.compile(str(src / rel), doraise=True)
    print(f"patched {len(files)} files, created {len(NEW_FILES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
