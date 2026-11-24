#!/usr/bin/env python3
"""Latency harness: private headless Sway + patched copy of an LME checkout.

usage: measure.py REPO OUT.json [--renderer gles2|pixman] [--scenario NAME]
Re-executes itself under dbus-run-session. Never touches the live session.
"""
import json, os, re, shutil, statistics, subprocess, sys, tempfile, time
from pathlib import Path

PATCHES = {
    'shell.qml': [
        ('target: "shell" // IPC surface for external toggles/scripts; keep names stable.',
         'target: "shell" // IPC surface for external toggles/scripts; keep names stable.\n'
         '        function tToggle(name: string): void { console.warn("TRACE toggle " + name + " " + Date.now()); ShellState.togglePanel(name); }\n'
         '        function tTab(id: string): void { console.warn("TRACE tab " + id + " " + Date.now()); ShellState.controlTab = ControlRegistry.indexForId(id); }\n'
         '        function tPage(key: string): void { console.warn("TRACE page " + key + " " + Date.now()); ShellState.settingsPage = key; }\n'
         '        function tState(): string { return JSON.stringify({ready: ShellState.backendReady, progress: panelLoader.progress, status: panelLoader.status, dormant: panelLoader.dormant, open: ShellState.panelOpen}); }'),
        ('        MouseArea { anchors.fill: parent; onClicked: ShellState.closePanels() }\n        Item {',
         '        MouseArea { anchors.fill: parent; onClicked: ShellState.closePanels() }\n'
         '        Connections { target: overlay.contentItem.Window.window; function onFrameSwapped() { console.warn("TRACE frame " + Date.now() + " " + panelLoader.progress.toFixed(3) + " " + (panelLoader.outsideViewport ? 0 : 1) + " " + panelLoader.status); } }\n'
         '        Item {'),
    ],
    'qml/components/SlideLoader.qml': [('    onLoaded: {\n', '    onLoaded: {\n        console.warn("TRACE slide-loaded " + Date.now());\n')],
    'qml/components/PageHost.qml': [('        previous.visible = false;', '        console.warn("TRACE page-activate " + Date.now());\n        previous.visible = false;')],
    'qml/settings/SettingsView.qml': [('            source: FeatureCatalog.url(root.currentPage.entry)\n',
                                       '            source: FeatureCatalog.url(root.currentPage.entry)\n            onLoaded: console.warn("TRACE catalog-loaded " + Date.now())\n')],
    'qml/panels/ControlCenter.qml': [('onLoaded: if (item && "embedded" in item) item.embedded = true }',
                                      'onLoaded: { console.warn("TRACE catalog-loaded " + Date.now()); if (item && "embedded" in item) item.embedded = true } }')],
}
# Optional patches: applied when the anchor exists (lets the same harness trace a modified tree).
OPTIONAL = {'qml/components/PageHost.qml', 'qml/settings/SettingsView.qml', 'qml/panels/ControlCenter.qml', 'qml/components/SlideLoader.qml'}


VARIANTS = {
    'sync': {
        'qml/components/PageHost.qml': [('asynchronous: true', 'asynchronous: false')] * 2,
        'qml/settings/SettingsView.qml': [('asynchronous: true', 'asynchronous: false')],
        'qml/panels/ControlCenter.qml': [('asynchronous: true', 'asynchronous: false')],
        'qml/components/SlideLoader.qml': [('    asynchronous: true', '    asynchronous: false')],
    },
}


def prepare(repo, root):
    for name in ('qml', 'scripts', 'config', 'assets'):
        shutil.copytree(repo / name, root / name, ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('shell.qml', 'settings.qml', 'settings-demo.qml'):
        shutil.copy(repo / name, root / name)
    for rel, edits in PATCHES.items():
        path = root / rel
        text = path.read_text()
        for old, new in edits:
            if old not in text:
                if rel in OPTIONAL:
                    print('note: anchor missing in', rel, file=sys.stderr); continue
                raise SystemExit('anchor missing in ' + rel + ': ' + old[:60])
            text = text.replace(old, new, 1)
        path.write_text(text)
    for rel, edits in VARIANTS.get(os.environ.get('LAT_VARIANT', ''), {}).items():
        path = root / rel; text = path.read_text()
        for old, new in edits:
            assert old in text, (rel, old); text = text.replace(old, new, 1)
        path.write_text(text)


def parse(log):
    events = []
    for line in log.splitlines():
        m = re.search(r'TRACE (\S+) (.*)$', line)
        if m: events.append((m.group(1), m.group(2).split()))
    return events


def analyze(events, kinds=('toggle', 'tab', 'page')):
    """For each action: ms to first frame showing ready content, and worst frame gap until settled."""
    out = []
    for i, (kind, args) in enumerate(events):
        if kind not in kinds: continue
        t0 = int(args[-1]); label = kind + ':' + args[0]
        ready_at = None; visible = None; settled = None; frames = []; prev = t0; gap = 0
        for k2, a2 in events[i + 1:]:
            if k2 in kinds: break
            if k2 in ('slide-loaded', 'page-activate', 'catalog-loaded', 'stack-ready'):
                ready_at = int(a2[0]); visible = None if kind != 'toggle' else visible
            if k2 == 'frame':
                t = int(a2[0]); frames.append(t); gap = max(gap, t - prev); prev = t
                progress, inside, status = float(a2[1]), a2[2] == '1', a2[3]
                if kind == 'toggle':
                    if visible is None and inside and status == '1' and progress > 0.02: visible = t
                    if settled is None and progress >= 0.99: settled = t
                elif ready_at is not None and visible is None: visible = t
        out.append({'action': label, 'ready_ms': ready_at - t0 if ready_at else None,
                    'first_content_frame_ms': visible - t0 if visible else None,
                    'settled_ms': settled - t0 if settled else None, 'max_frame_gap_ms': gap, 'frames': len(frames)})
    return out


def main():
    repo = Path(sys.argv[1]).resolve(); out_path = Path(sys.argv[2]).resolve()
    renderer = sys.argv[sys.argv.index('--renderer') + 1] if '--renderer' in sys.argv else 'gles2'
    scenario = sys.argv[sys.argv.index('--scenario') + 1] if '--scenario' in sys.argv else 'shell'
    if os.environ.get('LAT_INSIDE') != '1':
        work = Path(tempfile.mkdtemp(prefix='lme-lat-'))
        env = {k: v for k, v in os.environ.items() if not k.startswith(('WAYLAND', 'SWAYSOCK', 'DBUS_SESSION', 'NIRI', 'LME_'))}
        env.pop('DISPLAY', None)
        env.update(LAT_INSIDE='1', LAT_WORK=str(work), XDG_RUNTIME_DIR=str(work / 'rt'), XDG_CONFIG_HOME=str(work / 'cfg'),
                   XDG_STATE_HOME=str(work / 'state'), XDG_CACHE_HOME=str(work / 'cache'), XDG_DATA_HOME=str(work / 'data'),
                   DBUS_SYSTEM_BUS_ADDRESS='unix:path=' + str(work / 'nobus'), NIRI_SOCKET=str(work / 'no-niri'),
                   WLR_BACKENDS='headless', WLR_RENDERER=renderer, WLR_LIBINPUT_NO_DEVICES='1', LME_SHELL_DEMO='1',
                   QT_QPA_PLATFORM='wayland')
        if renderer == 'pixman': env.update(LIBGL_ALWAYS_SOFTWARE='1', QSG_RHI_BACKEND='opengl')
        for d in ('rt', 'cfg', 'state', 'cache', 'data'): (work / d).mkdir(mode=0o700, parents=True)
        code = subprocess.call(['dbus-run-session', '--', sys.executable, __file__] + sys.argv[1:], env=env)
        if code == 0 and not os.environ.get("LAT_KEEP"): shutil.rmtree(work, ignore_errors=True)
        else: print('kept', work, file=sys.stderr)
        raise SystemExit(code)
    work = Path(os.environ['LAT_WORK']); root = work / 'tree'; root.mkdir(); prepare(repo, root)
    (work / 'sway.conf').write_text('xwayland disable\noutput HEADLESS-1 mode 1920x1080@60Hz scale 1\nseat seat0 fallback true\n')
    sway = subprocess.Popen(['sway', '--config', str(work / 'sway.conf')], stdout=open(work / 'sway.log', 'w'), stderr=subprocess.STDOUT)
    rt = Path(os.environ['XDG_RUNTIME_DIR'])
    for _ in range(100):
        socks = [p for p in rt.glob('wayland-*') if p.is_socket()]
        if socks: os.environ['WAYLAND_DISPLAY'] = socks[0].name; break
        time.sleep(.05)
    results = {'renderer': renderer, 'scenario': scenario, 'runs': []}
    try:
        results['runs'] = SCENARIOS[scenario](root, work)
    finally:
        sway.terminate(); sway.wait(timeout=5)
    out_path.write_text(json.dumps(results, indent=1))
    print(json.dumps(summarize(results['runs']), indent=1))


def run_shell(root, work, steps, entry='shell.qml', extra_env=None):
    env = dict(os.environ, **(extra_env or {}))
    logf = open(work / 'qs.log', 'w+')
    proc = subprocess.Popen(['quickshell', '-p', str(root / entry)], env=env, stdout=logf, stderr=subprocess.STDOUT)
    def ipc(*args):
        return subprocess.check_output(['quickshell', '-p', str(root / entry), 'ipc', 'call', 'shell', *args], env=env, text=True, timeout=5).strip()
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                if json.loads(ipc('tState')).get('ready'): break
            except Exception: pass
            time.sleep(.1)
        for step in steps:
            if isinstance(step, (int, float)): time.sleep(step)
            else: ipc(*step)
        time.sleep(1.2)
        rss = [l for l in open(f'/proc/{proc.pid}/status') if l.startswith(('VmRSS', 'RssAnon'))]
        print('RSS', ' '.join(x.strip() for x in rss), file=sys.stderr)
    finally:
        proc.terminate(); proc.wait(timeout=10)
    logf.seek(0); log = logf.read()
    errors = [l for l in log.splitlines() if re.search(r'TypeError|ReferenceError|Binding loop|Unable to assign|Cannot read', l)]
    return analyze(parse(log)), errors[:20]


def close(): return ('close',)


def shell_scenario(root, work):
    tabs = ['audio', 'devices', 'agenda', 'monitor', 'controls']
    steps = [9]  # past both startup prewarms
    steps += [('tToggle', 'control'), 1.2, close(), 1.0] * 2
    steps += [('tToggle', 'notifications'), 1.2, close(), 1.0]
    steps += [('tToggle', 'control'), 1.2, close(), 1.0]
    steps += [('tToggle', 'control'), 1.2]
    for _ in range(2):
        for tab in tabs: steps += [('tTab', tab), 1.0]
    steps += [close(), 1.0]
    for name in ('launcher', 'clipboard', 'power', 'control', 'launcher'):
        steps += [('tToggle', name), 1.2, close(), 1.0]
    pages = ['appearance', 'elements', 'topbar', 'wallpaper', 'notifications', 'behavior', 'about', 'appearance', 'wallpaper']
    steps += [('tToggle', 'settings'), 1.5]
    for page in pages: steps += [('tPage', page), 1.0]
    steps += [close(), 1.0]
    runs = []
    for _ in range(int(os.environ.get('LAT_REPEAT', '1'))):
        result, errors = run_shell(root, work, steps)
        runs.append({'actions': result, 'errors': errors})
    return runs


SCENARIOS = {'shell': shell_scenario}


def summarize(runs):
    rows = {}
    for run in runs:
        for idx, a in enumerate(run['actions']):
            rows.setdefault((idx, a['action']), []).append(a)
    out = []
    for (idx, action), items in sorted(rows.items()):
        def med(key):
            vals = [i[key] for i in items if i[key] is not None]
            return round(statistics.median(vals)) if vals else None
        out.append(f"{idx:02d} {action:24s} ready={med('ready_ms')} content={med('first_content_frame_ms')} settled={med('settled_ms')} gap={med('max_frame_gap_ms')}")
    if runs and runs[0]['errors']: out.append('errors: ' + ' | '.join(runs[0]['errors'][:5]))
    return out


if __name__ == '__main__':
    main()
