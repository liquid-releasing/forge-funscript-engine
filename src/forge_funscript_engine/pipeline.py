"""Pipeline: input funscript actions -> device channel funscripts.

    actions -> analyze (section 3) -> derive Feel (section 3.2)
            -> [POLISH] condition into device channels -> safety clamp (section 9)

Two device paths:
  - e-stim (`generate_estim`)       -> alpha/beta/volume (+ full superset), section 7
  - single-axis (`generate_single_axis`) -> one position track, section 8

E-stim is chapter-aware: each chapter derives its own Feel and channels, then seams
are stitched so the per-seam delta stays within the safety envelope (section 7.5).
"""
import os

from .analyze import analyze, DT_MS
from .feel import derive_feel, ramp_slice
from .estim import derive_channels, MINIMAL, FULL, RISE_TIME
from .singleaxis import build_device
from .chapters import equal_chapters, slice_actions, stitch
from .safety import encode_pos, rate_limit, channel_ceiling, POS_MAX
from .funscript import Funscript, dump_funscript

CHANNELS = MINIMAL   # the minimal playable set (back-compat alias)

# safe per-channel resting value for empty / single-point input (section 3.4)
_SAFE = {"alpha": 0.5, "beta": 0.5, "alpha-prostate": 0.5, "frequency": 0.5}


def _channel_names(full, enable_rise_time):
    names = list(FULL if full else MINIMAL)
    if full and enable_rise_time:
        names.append(RISE_TIME)
    return names


def _encode_channel(name, values, t0):
    ceiling = channel_ceiling(name)
    if name.startswith("volume"):
        values = rate_limit(values)   # section 9 smooth-ramp cap on current-bearing channels
    acts = [{"at": int(t0 + i * DT_MS), "pos": encode_pos(v, ceiling)}
            for i, v in enumerate(values)]
    return Funscript(actions=acts)


def _safe_frames(names):
    return {n: Funscript(actions=[{"at": 0, "pos": encode_pos(_SAFE.get(n, 0.0),
                                                              channel_ceiling(n))}])
            for n in names}


def _chapter_action_lists(actions, chapters):
    if not chapters:
        return [actions]
    if isinstance(chapters, int):
        return equal_chapters(actions, chapters)
    return [slice_actions(actions, s, e) for (s, e) in chapters]


def generate_estim(actions, ramp=None, name="out", out_dir=None,
                   chapters=None, full=True, enable_rise_time=False):
    """Generate the e-stim channel set. `chapters` may be None (one chapter), an int
    (split into N equal chapters), or a list of (start_ms, end_ms) windows.

    Returns {channel: Funscript}; writes <out_dir>/estim/<name>.<channel>.funscript
    if out_dir is given.
    """
    names = _channel_names(full, enable_rise_time)
    parts = []
    for ca in _chapter_action_lists(actions, chapters):
        sig = analyze(ca)
        if sig.n_samples < 2:
            continue
        R = ramp_slice(sig.T_s) if ramp is None else ramp
        feel = derive_feel(sig, R)
        parts.append((ca, derive_channels(sig, feel, R, full, enable_rise_time)))

    if not parts:
        channels = _safe_frames(names)
    else:
        boundaries, cum = [], 0
        concat = {n: [] for n in names}
        for idx, (_, ch) in enumerate(parts):
            if idx > 0:
                boundaries.append(cum)
            for n in names:
                concat[n].extend(ch[n])
            cum += len(ch["alpha"])
        t0 = parts[0][0][0]["at"]
        channels = {n: _encode_channel(n, stitch(concat[n], boundaries), t0)
                    for n in names}

    if out_dir is not None:
        _write(channels, os.path.join(out_dir, "estim"), name)
    return channels


def generate_single_axis(actions, device="handy", knobs=None,
                         name="out", out_dir=None):
    """Generate one conditioned position track for a single-axis stroker (section 8).

    Returns {"position": Funscript}; writes <out_dir>/<device>/<name>.funscript.
    """
    sig = analyze(actions)
    if sig.n_samples < 2:
        position = Funscript(actions=[{"at": 0, "pos": 50}])
    else:
        feel = derive_feel(sig)
        pos = build_device(sig.xs, feel, device, knobs)
        t0 = actions[0]["at"]
        position = Funscript(actions=[
            {"at": int(t0 + i * DT_MS), "pos": encode_pos(v, POS_MAX)}
            for i, v in enumerate(pos)
        ])
    channels = {"position": position}
    if out_dir is not None:
        dev_dir = os.path.join(out_dir, device)
        os.makedirs(dev_dir, exist_ok=True)
        dump_funscript(position, os.path.join(dev_dir, f"{name}.funscript"))
    return channels


def _write(channels, target_dir, name):
    os.makedirs(target_dir, exist_ok=True)
    for ch, fs in channels.items():
        dump_funscript(fs, os.path.join(target_dir, f"{name}.{ch}.funscript"))
