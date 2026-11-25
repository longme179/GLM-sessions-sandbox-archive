#!/usr/bin/env python3
"""Agent-2: analyze the round-2 Settings stutter probe runs (stock vs fixed).

Input:  a directory holding the fetched runs: <runs>/<run>/probe.log, meta.json, samples.json,
        pointer.log (use scripts/host_fetch.py to pull them from /tmp/lme-probe2/runs on the host)
Output: a text report on stdout and analysis2.json next to the runs

  python3 -I probe_analyze2.py /home/z/my-project/probe_runs2 [--only stock-use,fixed-use]

Event grammar (probe_patch2.py / Probe.qml v2); all times are ms since the probe singleton started:
  start epoch=.. mono=.. hires=.. noprewarm=.. nopoll=.. script=.. runMs=..
  m <t> <label> [arg with spaces]    marks: app.completed, view.completed, view.status, window.visible,
                                     prepared, t0.firstpage, present, request, drop, page.status,
                                     prewarm.armed, script.<tag> "... call=<ms>", quit
  s <t> key=value                    state change          F <t>        rendered frame (frameSwapped)
  g <t> <gap>                        GUI-thread timer gap >= 9.5 ms starting at t
  b <t> <page> resolve= build= async=true|false     page entry (sync build time inside)
  l <t> <page>                       page loaded (onLoaded)   k <t> left=N gated=true|false  prewarm tick
  a <t> parse= identity= assign= snapshot= tail= bytes= action=NAME
  r/q/x <t> <action>                 backend run / sent / blocked
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HITCH_MS, FREEZE_MS = 40.0, 100.0
ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[()][0-9A-B]|\r")
PROBE = re.compile(r"@@PROBE (.*)$")
PROBLEM_WORDS = ("ERROR", "WARNING", "is not a", "Expected token", "Unable", "Cannot assign", "binding loop",
                 "TypeError", "ReferenceError", "is not defined")
KNOWN_NOISE = ("Failed to connect pipewire context",)
TICK_MS = 1000.0 / 100.0  # replaced from os.sysconf at run time
NUM = re.compile(r"^-?\d+(\.\d+)?$")


def num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def kv(tokens):
    out = {}
    for token in tokens:
        key, sep, value = token.partition("=")
        if sep:
            out[key] = value
    return out


def parse_run(run_dir: Path):
    events, problems = [], set()
    for line in (run_dir / "probe.log").read_text(errors="replace").splitlines():
        clean = ANSI.sub("", line).strip()
        found = PROBE.search(clean)
        if not found:
            if any(word in clean for word in PROBLEM_WORDS) and not any(noise in clean for noise in KNOWN_NOISE):
                problems.add(clean[:220])
            continue
        parts = found.group(1).split()
        kind, rest = parts[0], parts[1:]
        t = num(rest[0]) if rest and NUM.match(rest[0]) else 0.0
        if kind == "F":
            entry = {"k": "F", "t": t}
        elif kind == "g":
            entry = {"k": "g", "t": t, "gap": num(rest[1])}
        elif kind == "m":
            entry = {"k": "m", "t": t, "label": rest[1], "arg": " ".join(rest[2:])}
        elif kind == "s":
            key, _, value = rest[1].partition("=")
            entry = {"k": "s", "t": t, "key": key, "value": value}
        elif kind in ("b", "t"):
            entry = {"k": kind, "t": t, "page": rest[1], **kv(rest[2:])}
        elif kind == "l":
            entry = {"k": "l", "t": t, "page": rest[1]}
        elif kind == "k":
            entry = {"k": "k", "t": t, **kv(rest[1:])}
        elif kind in ("r", "q", "x"):
            entry = {"k": kind, "t": t, "action": rest[1]}
        elif kind == "a":
            entry = {"k": "a", "t": t, "sections": ""}
            for token in rest[1:]:
                key, sep, value = token.partition("=")
                if sep:
                    entry[key] = value
        elif kind == "start":
            entry = {"k": "start", "t": 0.0, **kv(rest)}
        else:
            continue
        events.append(entry)
    events.sort(key=lambda e: e["t"])
    meta = json.loads((run_dir / "meta.json").read_text()) if (run_dir / "meta.json").exists() else {}
    return events, meta, sorted(problems)


def marks(events, label):
    return [e for e in events if e["k"] == "m" and e["label"] == label]


def first_mark(events, label, arg=None):
    for e in marks(events, label):
        if arg is None or e["arg"].startswith(arg):
            return e
    return None


def call_ms(mark):
    found = re.search(r"call=([\d.]+)", mark["arg"])
    return num(found.group(1)) if found else None


# ---- busy intervals on the GUI thread, for attributing stalls ----------------------------------
def busy_intervals(events):
    """(start, end, label) of everything that is known to occupy the GUI thread."""
    loads = defaultdict(list)
    for e in events:
        if e["k"] == "l":
            loads[e["page"]].append(e["t"])
    dropped = {}
    for e in marks(events, "drop"):
        dropped.setdefault(e["arg"].split()[0], []).append(e["t"])
    intervals = []
    for e in events:
        if e["k"] == "b":
            resolve, build = num(e.get("resolve")), num(e.get("build"))
            total = resolve + build
            if e.get("async") == "true":
                end = next((t for t in loads.get(e["page"], []) if t >= e["t"]), None)
                stop = next((t for t in dropped.get(e["page"], []) if t >= e["t"]), None)
                if stop is not None and (end is None or stop < end):
                    end, label = stop, f"incubation {e['page']} (dropped)"
                else:
                    label = f"incubation {e['page']}"
                if end is None:
                    continue
                intervals.append((e["t"], end, label))
            elif total > 0:
                intervals.append((e["t"], e["t"] + total, f"sync build {e['page']} {total:.0f}ms"))
        elif e["k"] == "a":
            total = sum(num(e.get(key)) for key in ("parse", "identity", "assign", "snapshot", "tail"))
            intervals.append((e["t"], e["t"] + total, f"snapshot apply {e.get('action') or '?'} {total:.0f}ms"))
        elif e["k"] == "m" and e["label"].startswith("script."):
            cost = call_ms(e) or 0.0
            intervals.append((e["t"], e["t"] + max(cost, 0.1), f"{e['label']} call={cost:.1f}ms"))
    return intervals


def attribute(gap, intervals):
    best = None
    for start, end, label in intervals:
        overlap = min(end, gap["t"] + gap["gap"]) - max(start, gap["t"])
        if overlap > 0 and (best is None or overlap > best[0]):
            best = (overlap, label)
    return f"{best[1]} (overlap {best[0]:.0f}ms)" if best else "unattributed"


def window_stats(events, intervals, lo, hi):
    gaps = [g for g in events if g["k"] == "g" and lo <= g["t"] < hi]
    frames = [f["t"] for f in events if g_is_frame(f) and lo <= f["t"] < hi]
    gaps.sort(key=lambda g: -g["gap"])
    out = {
        "ms": round(hi - lo),
        "hitches": len([g for g in gaps if g["gap"] >= HITCH_MS]),
        "freezes": len([g for g in gaps if g["gap"] >= FREEZE_MS]),
        "stall_ms": round(sum(g["gap"] for g in gaps if g["gap"] >= HITCH_MS)),
        "max_gap": round(gaps[0]["gap"]) if gaps else 0,
        "frames": len(frames),
    }
    out["worst"] = [{"at": round(g["t"]), "gap": round(g["gap"]), "cause": attribute(g, intervals)}
                    for g in gaps if g["gap"] >= HITCH_MS][:8]
    return out


def g_is_frame(e):
    return e["k"] == "F"


def scroll_stats(events, intervals, mark, duration):
    lo, hi = mark["t"], mark["t"] + duration
    stats = window_stats(events, intervals, lo, hi)
    frames = [f["t"] for f in events if f["k"] == "F" and lo <= f["t"] < hi]
    deltas = [b - a for a, b in zip(frames, frames[1:])]
    deltas.sort()
    stats.update({
        "fps": round(len(frames) / (duration / 1000.0), 1),
        "max_frame_interval": round(deltas[-1]) if deltas else None,
        "p95_frame_interval": round(deltas[int(len(deltas) * 0.95)]) if deltas else None,
    })
    del stats["ms"]
    return stats


def cpu_by_thread(run_dir: Path, lo_s, hi_s):
    path = run_dir / "samples.json"
    if not path.exists():
        return {}
    total = Counter()
    for at, threads in json.loads(path.read_text()):
        if lo_s <= at < hi_s:
            for name, ticks in threads.items():
                total[name] += ticks
    return {name: round(ticks * TICK_MS / 1000.0, 2) for name, ticks in total.items()}


def analyze(run_dir: Path):
    events, meta, problems = parse_run(run_dir)
    intervals = busy_intervals(events)
    start = next((e for e in events if e["k"] == "start"), None)
    out = {"run": run_dir.name, "variant": "fixed" if "fixed" in str(meta.get("src", "")) else "stock",
           "script": meta.get("script"), "live": meta.get("live"), "pointer": meta.get("pointer")}
    epoch = num(start.get("epoch")) if start else None
    launch_to_probe = None
    if epoch and meta.get("launch_wall"):
        launch_to_probe = epoch - meta["launch_wall"] * 1000.0
    out["launch_to_probe_ms"] = round(launch_to_probe) if launch_to_probe is not None else None

    # ---- startup ----
    def probe_to_launch(t):
        return round(t + launch_to_probe) if (launch_to_probe is not None and t is not None) else None

    def state_time(key, value="true"):
        return next((e["t"] for e in events if e["k"] == "s" and e["key"] == key and e["value"] == value), None)

    visible = first_mark(events, "window.visible", "true")
    first_frame = next((f["t"] for f in events if f["k"] == "F" and visible and f["t"] >= visible["t"]), None)
    first_page = next((e for e in events if e["k"] == "b"), None)
    first_load = next((e for e in events if e["k"] == "l"), None)
    t0_mark = first_mark(events, "t0.firstpage")
    t0 = t0_mark["t"] if t0_mark else (first_load["t"] if first_load else 0.0)
    startup = {
        "view_completed": (first_mark(events, "view.completed") or {}).get("t"),
        "view_ready": next((e["t"] for e in marks(events, "view.status") if e["arg"].startswith("Ready")), None),
        "first_page": first_page["page"] if first_page else None,
        "first_page_resolve_build_ms": [round(num(first_page.get("resolve"))), round(num(first_page.get("build")))] if first_page else None,
        "first_page_loaded": first_load["t"] if first_load else None,
        "window_visible": visible["t"] if visible else None,
        "first_frame": first_frame,
        "launch_to_first_frame_ms": probe_to_launch(first_frame),
    }
    startup = {k: (round(v) if isinstance(v, float) else v) for k, v in startup.items()}
    out["startup"] = startup
    out["t0"] = round(t0)

    # ---- phases ----
    phases = {}
    end = events[-1]["t"] if events else t0
    hide1, show1 = first_mark(events, "script.hide1"), first_mark(events, "script.show1")
    hide2, show2 = first_mark(events, "script.hide2"), first_mark(events, "script.show2")
    script = meta.get("script")
    phases["first 2s"] = (t0, t0 + 2000)
    phases["first 8s"] = (t0, t0 + 8000)
    phases["first 20s"] = (t0, min(t0 + 20000, hide1["t"] if hide1 else end))
    if script == "use":
        phases["use (open→hide1)"] = (t0, hide1["t"]) if hide1 else (t0, end)
        warm = []
        if show1 and hide2:
            warm.append((show1["t"], hide2["t"]))
        if show2:
            warm.append((show2["t"], end))
        phases["warm (pages built)"] = warm
    elif script == "idle":
        phases["idle (open→hide1)"] = (t0, hide1["t"]) if hide1 else (t0, end)
    else:
        phases[f"{script} (whole run)"] = (t0, end)
    out["phases"] = {}
    for name, span in phases.items():
        spans = span if isinstance(span, list) else [span]
        stats = [window_stats(events, intervals, lo, hi) for lo, hi in spans if hi > lo]
        merged = {
            "ms": sum(s["ms"] for s in stats),
            "hitches": sum(s["hitches"] for s in stats),
            "freezes": sum(s["freezes"] for s in stats),
            "stall_ms": sum(s["stall_ms"] for s in stats),
            "max_gap": max((s["max_gap"] for s in stats), default=0),
            "frames": sum(s["frames"] for s in stats),
        }
        merged["worst"] = sorted((w for s in stats for w in s["worst"]), key=lambda w: -w["gap"])[:10]
        merged["hitches_per_s"] = round(merged["hitches"] / (merged["ms"] / 1000.0), 2) if merged["ms"] else None
        out["phases"][name] = merged

    # ---- scrolls / navigation / typing ----
    scrolls, navs, types = [], [], []
    for mark in (e for e in events if e["k"] == "m" and str(e.get("label", "")).startswith("script.")):
        tag = mark["label"].split(".", 1)[1]
        if tag.startswith("scroll"):
            index = int(tag[6:])
            scrolls.append({"tag": tag, "at": round(mark["t"] - t0), "call": call_ms(mark),
                            **scroll_stats(events, intervals, mark, 800 if index % 2 else 600)})
        elif tag.startswith(("nav", "cold")):
            key = (re.search(r"->(\S+)", mark["arg"]) or [None, None])[1]
            build = next((b for b in events if b["k"] == "b" and b["page"] == key and abs(b["t"] - mark["t"]) < 400), None)
            loaded = next((l for l in events if l["k"] == "l" and l["page"] == key and 0 <= l["t"] - mark["t"] < 5000), None)
            presented = next((p for p in marks(events, "present") if p["arg"].startswith(key)
                              and 0 <= p["t"] - mark["t"] < 5000), None)
            after = [g for g in events if g["k"] == "g" and 0 <= g["t"] - mark["t"] < 3000]
            navs.append({
                "tag": tag, "key": key, "at": round(mark["t"] - t0), "call": call_ms(mark),
                "build": ([round(num(build.get("resolve")) + num(build.get("build"))), build.get("async")] if build else None),
                "shown_after_ms": round((presented or loaded)["t"] - mark["t"]) if (presented or loaded) else None,
                "max_gap_next_3s": round(max((g["gap"] for g in after), default=0)),
            })
        elif tag.startswith("type"):
            types.append({"tag": tag, "at": round(mark["t"] - t0), "call": call_ms(mark)})
    if scrolls:
        out["scrolls"] = scrolls
        out["scroll_summary"] = {
            "count": len(scrolls),
            "fps_min": min(s["fps"] for s in scrolls), "fps_mean": round(sum(s["fps"] for s in scrolls) / len(scrolls), 1),
            "max_frame_interval": max(s["max_frame_interval"] or 0 for s in scrolls),
            "hitches": sum(s["hitches"] for s in scrolls), "freezes": sum(s["freezes"] for s in scrolls),
            "stall_ms": sum(s["stall_ms"] for s in scrolls),
        }
    if navs:
        out["navs"] = navs
        out["nav_summary"] = {"max_call": max(n["call"] or 0 for n in navs), "max_gap_next_3s": max(n["max_gap_next_3s"] for n in navs)}
    if types:
        out["typing"] = types
        out["typing_summary"] = {"max_call": round(max(t["call"] or 0 for t in types), 1),
                                 "mean_call": round(sum(t["call"] or 0 for t in types) / len(types), 1)}

    # ---- hide / show ----
    cycles = []
    for index in (1, 2):
        hide, show = first_mark(events, f"script.hide{index}"), first_mark(events, f"script.show{index}")
        if not hide or not show:
            continue
        hid = next((e for e in marks(events, "window.visible") if e["arg"] == "false" and e["t"] >= hide["t"]), None)
        shown = next((e for e in marks(events, "window.visible") if e["arg"] == "true" and e["t"] >= show["t"]), None)
        frame = next((f["t"] for f in events if f["k"] == "F" and shown and f["t"] >= shown["t"]), None)
        cycles.append({
            "hide_at": round(hide["t"] - t0), "hide_call": call_ms(hide),
            "hide_to_invisible": round(hid["t"] - hide["t"]) if hid else None,
            "stalls_1s_after_hide": window_stats(events, intervals, hide["t"], hide["t"] + 1000),
            "show_at": round(show["t"] - t0), "show_call": call_ms(show),
            "show_to_visible": round(shown["t"] - show["t"]) if shown else None,
            "show_to_first_frame": round(frame - show["t"]) if frame else None,
            "stalls_1s_after_show": window_stats(events, intervals, show["t"], show["t"] + 1000),
        })
    if cycles:
        out["hide_show"] = cycles

    # ---- builds / walk ----
    builds = []
    for e in events:
        if e["k"] != "b":
            continue
        loaded = next((l for l in events if l["k"] == "l" and l["page"] == e["page"] and l["t"] >= e["t"]), None)
        builds.append({"page": e["page"], "at": round(e["t"] - t0), "resolve": round(num(e.get("resolve")), 1),
                       "build": round(num(e.get("build")), 1), "async": e.get("async"),
                       "loaded_after": round(loaded["t"] - e["t"]) if loaded else None})
    out["builds"] = builds
    out["walk"] = {
        "pages_built": len(builds),
        "first_background_start": next((b["at"] for b in builds[1:]), None) if len(builds) > 1 else None,
        "last_loaded_at": max((round(l["t"] - t0) for l in events if l["k"] == "l"), default=None),
        "sync_total_ms": round(sum(b["resolve"] + b["build"] for b in builds if b["async"] != "true")),
        "sync_max_ms": max((b["resolve"] + b["build"] for b in builds if b["async"] != "true"), default=0),
        "async_count": len([b for b in builds if b["async"] == "true"]),
        "async_span_max_ms": max((b["loaded_after"] or 0 for b in builds if b["async"] == "true"), default=0),
    }
    ticks = [e for e in events if e["k"] == "k"]
    if ticks:
        out["gate"] = {"ticks": len(ticks), "gated": len([e for e in ticks if e.get("gated") == "true"]),
                       "first_tick_at": round(ticks[0]["t"] - t0),
                       "first_open_tick_at": next((round(e["t"] - t0) for e in ticks if e.get("gated") == "false"), None)}
    drops = [d for d in marks(events, "drop")]
    if drops:
        out["drops"] = [{"at": round(d["t"] - t0), "what": d["arg"]} for d in drops]
    activity = len([e for e in events if e["k"] == "s" and e["key"] == "activity"])
    out["activity_changes"] = activity or None

    # ---- backend snapshots ----
    per_action = defaultdict(lambda: {"n": 0, "total": 0.0, "max": 0.0, "parse": 0.0, "identity": 0.0, "assign": 0.0,
                                      "snapshot": 0.0, "tail": 0.0, "max_tail": 0.0})
    slowest = []
    for e in events:
        if e["k"] != "a":
            continue
        parts = {key: num(e.get(key)) for key in ("parse", "identity", "assign", "snapshot", "tail")}
        total = sum(parts.values())
        d = per_action[e.get("action") or "?"]
        d["n"] += 1
        d["total"] += total
        d["max"] = max(d["max"], total)
        d["max_tail"] = max(d["max_tail"], parts["tail"])
        for key, value in parts.items():
            d[key] += value
        slowest.append({"at": round(e["t"] - t0), "action": e.get("action"), "total": round(total, 1),
                        "bytes": e.get("bytes"), **{k: round(v, 1) for k, v in parts.items()}})
    out["snapshots"] = {k: {kk: round(vv, 1) for kk, vv in v.items()} for k, v in
                        sorted(per_action.items(), key=lambda kv: -kv[1]["max"])[:8]}
    out["slowest_snapshots"] = sorted(slowest, key=lambda s: -s["total"])[:5]

    # ---- CPU ----
    t0_s = (t0 + (launch_to_probe or 0)) / 1000.0
    out["cpu_s"] = {
        "startup": dict(sorted(cpu_by_thread(run_dir, 0, t0_s).items(), key=lambda kv: -kv[1])[:6]),
        "first_20s": dict(sorted(cpu_by_thread(run_dir, t0_s, t0_s + 20).items(), key=lambda kv: -kv[1])[:6]),
    }
    out["problems"] = problems
    out["frames_total"] = len([e for e in events if e["k"] == "F"])
    return out


def fmt_stats(stats):
    return (f"hitches≥40ms {stats['hitches']:>3}  freezes≥100ms {stats['freezes']:>2}  stalled "
            f"{stats['stall_ms']:>5} ms  max {stats['max_gap']:>4} ms  frames {stats['frames']:>5}")


def print_run(data):
    line = (f"RUN {data['run']}  [{data['variant']} / {data['script']}{' / live' if data['live'] else ''}"
            f"{' / pointer' if data['pointer'] else ''}]")
    print("\n" + "=" * 100 + "\n" + line + "\n" + "=" * 100)
    s = data["startup"]
    print(f"startup: launch→probe {data['launch_to_probe_ms']} ms | view Ready +{s['view_ready']} | window visible +{s['window_visible']}"
          f" | first frame +{s['first_frame']}  => launch→first frame {s['launch_to_first_frame_ms']} ms"
          f" | first page {s['first_page']} resolve/build {s['first_page_resolve_build_ms']}")
    print("phases (GUI-thread stalls from the 4 ms heartbeat; frames = frameSwapped):")
    for name, stats in data["phases"].items():
        print(f"  {name:<22} {fmt_stats(stats)}")
        for worst in stats["worst"][:4]:
            print(f"      {'':<4} t0+{worst['at'] - data['t0']:>6}  gap {worst['gap']:>4} ms  {worst['cause']}")
    if data.get("scroll_summary"):
        ssum = data["scroll_summary"]
        print(f"scrolls: {ssum['count']} windows, fps min {ssum['fps_min']} mean {ssum['fps_mean']}, worst frame interval "
              f"{ssum['max_frame_interval']} ms, hitches {ssum['hitches']}, freezes {ssum['freezes']}, stalled {ssum['stall_ms']} ms")
        for s in data["scrolls"]:
            print(f"    {s['tag']:<9} t0+{s['at']:>6} call {str(s['call']):>6}  fps {str(s['fps']):>5}  interval max {str(s['max_frame_interval']):>4}"
                  f" p95 {str(s['p95_frame_interval']):>4}  hitches {s['hitches']} freezes {s['freezes']} stalled {s['stall_ms']}")
    if data.get("navs"):
        print(f"navigation: max call {data['nav_summary']['max_call']} ms, worst stall in the 3 s after {data['nav_summary']['max_gap_next_3s']} ms")
        for n in data["navs"]:
            print(f"    {n['tag']:<6} → {n['key']:<11} t0+{n['at']:>6}  call {n['call']:>6}  build(async) {n['build']}  "
                  f"shown +{n['shown_after_ms']} ms  worst stall next 3 s {n['max_gap_next_3s']} ms")
    if data.get("typing"):
        print(f"typing: max call {data['typing_summary']['max_call']} ms, mean {data['typing_summary']['mean_call']} ms  "
              + " ".join(f"{t['tag']}={t['call']}" for t in data["typing"]))
    for cycle in data.get("hide_show", []):
        print(f"hide/show: hide t0+{cycle['hide_at']} call {cycle['hide_call']} → invisible +{cycle['hide_to_invisible']} ms"
              f" | {fmt_stats(cycle['stalls_1s_after_hide'])}")
        print(f"           show t0+{cycle['show_at']} call {cycle['show_call']} → visible +{cycle['show_to_visible']} ms"
              f" → first frame +{cycle['show_to_first_frame']} ms | {fmt_stats(cycle['stalls_1s_after_show'])}")
    walk = data["walk"]
    print(f"builds: {walk['pages_built']} pages, first background start t0+{walk['first_background_start']}, last loaded t0+{walk['last_loaded_at']}"
          f" | sync {walk['sync_total_ms']} ms total, max {walk['sync_max_ms']} ms | async {walk['async_count']} pages, longest span {walk['async_span_max_ms']} ms")
    print("  " + "  ".join(f"{b['page']}@{b['at']}:{'a' if b['async'] == 'true' else 's'}{b['resolve'] + b['build']:.0f}"
                            + (f"/{b['loaded_after']}" if b['async'] == 'true' and b['loaded_after'] is not None else "")
                            for b in data["builds"]))
    if data.get("gate"):
        print(f"gate: {data['gate']['ticks']} ticks, {data['gate']['gated']} gated; first tick t0+{data['gate']['first_tick_at']},"
              f" first open tick t0+{data['gate']['first_open_tick_at']}")
    for drop in data.get("drops", [])[:12]:
        print(f"  drop t0+{drop['at']} {drop['what']}")
    if data.get("activity_changes"):
        print(f"activity changes: {data['activity_changes']}")
    print("backend snapshots (ms):")
    for action, d in data["snapshots"].items():
        print(f"  {action:<22} n={d['n']:>3} total {d['total']:>8} max {d['max']:>6} (parse {d['parse']}, identity {d['identity']},"
              f" assign {d['assign']}, snapshot {d['snapshot']}, tail {d['tail']} maxTail {d['max_tail']}")
    print(f"frames total {data['frames_total']}; CPU seconds by thread: startup {data['cpu_s']['startup']} | first 20 s {data['cpu_s']['first_20s']}")
    print(f"problem lines: {len(data['problems'])}")
    for line in data["problems"][:8]:
        print("  " + line)


def compare(results):
    names = [r["run"] for r in results]
    print("\n" + "=" * 100 + "\nCOMPARISON\n" + "=" * 100)

    def row(label, values):
        print(f"{label:<34}" + "".join(f"{str(v):>24}" for v in values))

    row("metric", names)
    row("launch → first frame (ms)", [r["startup"]["launch_to_first_frame_ms"] for r in results])
    row("first frame after open → pg", [r["startup"]["first_page"] for r in results])
    row("first page resolve/build (ms)", [r["startup"]["first_page_resolve_build_ms"] for r in results])
    for phase in results[0]["phases"]:
        row(f"{phase}: hitches ≥40ms", [r["phases"].get(phase, {}).get("hitches") for r in results])
        row(f"{phase}: freezes ≥100ms", [r["phases"].get(phase, {}).get("freezes") for r in results])
        row(f"{phase}: stalled ms", [r["phases"].get(phase, {}).get("stall_ms") for r in results])
        row(f"{phase}: max gap ms", [r["phases"].get(phase, {}).get("max_gap") for r in results])
    if any(r.get("scroll_summary") for r in results):
        row("scroll fps min", [r.get("scroll_summary", {}).get("fps_min") for r in results])
        row("scroll fps mean", [r.get("scroll_summary", {}).get("fps_mean") for r in results])
        row("scroll worst frame interval ms", [r.get("scroll_summary", {}).get("max_frame_interval") for r in results])
        row("scroll stalled ms", [r.get("scroll_summary", {}).get("stall_ms") for r in results])
        row("scroll hitches", [r.get("scroll_summary", {}).get("hitches") for r in results])
        row("scroll freezes", [r.get("scroll_summary", {}).get("freezes") for r in results])
    if any(r.get("navs") for r in results):
        row("nav max call ms", [r.get("nav_summary", {}).get("max_call") for r in results])
        row("nav worst stall next 3 s ms", [r.get("nav_summary", {}).get("max_gap_next_3s") for r in results])
    if any(r.get("typing") for r in results):
        row("typing max call ms", [r.get("typing_summary", {}).get("max_call") for r in results])
        row("typing mean call ms", [r.get("typing_summary", {}).get("mean_call") for r in results])
    if any(r.get("hide_show") for r in results):
        for index in (0, 1):
            row(f"show{index + 1} → first frame ms", [(r.get("hide_show") or [None] * 2)[index]["show_to_first_frame"] if len(r.get("hide_show") or []) > index else None for r in results])
            row(f"hide{index + 1} stalls ≥40ms (1 s)", [(r.get("hide_show") or [None] * 2)[index]["stalls_1s_after_hide"]["hitches"] if len(r.get("hide_show") or []) > index else None for r in results])
            row(f"hide{index + 1} stalled ms (1 s)", [(r.get("hide_show") or [None] * 2)[index]["stalls_1s_after_hide"]["stall_ms"] if len(r.get("hide_show") or []) > index else None for r in results])
    row("pages built / last loaded (t0+ms)", [f"{r['walk']['pages_built']} / {r['walk']['last_loaded_at']}" for r in results])
    row("sync build total ms (max)", [f"{r['walk']['sync_total_ms']} ({r['walk']['sync_max_ms']})" for r in results])
    row("frames total", [r["frames_total"] for r in results])
    row("problem lines", [len(r["problems"]) for r in results])


def main():
    global TICK_MS
    import os
    TICK_MS = 1000.0 / os.sysconf("SC_CLK_TCK")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="?", default="/home/z/my-project/probe_runs2/runs")
    parser.add_argument("--only", help="comma separated run names")
    parser.add_argument("--no-detail", action="store_true")
    parser.add_argument("--json", help="where to write the JSON summary (default <runs>/analysis2.json)")
    args = parser.parse_args()
    base = Path(args.runs)
    only = set(args.only.split(",")) if args.only else None
    results = []
    for run_dir in sorted(base.iterdir()):
        if not (run_dir / "probe.log").exists() or (only and run_dir.name not in only):
            continue
        try:
            results.append(analyze(run_dir))
        except Exception as error:  # noqa: BLE001 - one broken run must not hide the others
            print(f"FAILED {run_dir.name}: {error!r}")
    if not results:
        sys.exit("no runs analyzed")
    (Path(args.json) if args.json else base / "analysis2.json").write_text(json.dumps(results, indent=1))
    if not args.no_detail:
        for data in results:
            print_run(data)
    if len(results) > 1:
        compare(results)


if __name__ == "__main__":
    main()
