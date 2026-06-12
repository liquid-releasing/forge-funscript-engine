"""Phase-1 pipeline: input funscript actions -> e-stim alpha/beta/volume funscripts.

    actions -> analyze (section 3) -> derive Feel (section 3.2)
            -> lift (section 7.2) -> safety clamp (section 9) -> funscript channels

Minimal playable set = alpha + beta + volume (spec section 7.1). The remaining
e-stim channels and single-axis profiles are Phase 2.
"""
import os

from .analyze import analyze, DT_MS
from .feel import derive_feel, ramp_slice
from .lift import lift
from .safety import rate_limit, encode_pos, CH_MAX, MAX_VOLUME
from .funscript import Funscript, dump_funscript

CHANNELS = ("alpha", "beta", "volume")


def _safe_frame_channels():
    """Output for empty / single-point input: one safe centered frame
    (alpha=beta=0.5 decoded, volume silent). Spec section 3.4 / tests/README."""
    return {
        "alpha": Funscript(actions=[{"at": 0, "pos": encode_pos(0.5)}]),
        "beta": Funscript(actions=[{"at": 0, "pos": encode_pos(0.5)}]),
        "volume": Funscript(actions=[{"at": 0, "pos": encode_pos(0.0, MAX_VOLUME)}]),
    }


def generate_estim(actions, ramp=None, name="out", out_dir=None):
    """Generate the Phase-1 e-stim channel set from input stroke `actions`.

    Returns {channel: Funscript}. If `out_dir` is given, also writes
    `<out_dir>/estim/<name>.<channel>.funscript`.
    """
    sig = analyze(actions)
    if sig.n_samples < 2:
        channels = _safe_frame_channels()
    else:
        R = ramp_slice(sig.T_s) if ramp is None else ramp
        feel = derive_feel(sig, R)
        decoded = lift(sig, feel, R)
        # Section 9: rate-limit volume BEFORE encoding (smooth-ramp requirement).
        decoded["volume"] = rate_limit(decoded["volume"])

        t0 = actions[0]["at"]
        channels = {}
        for ch in CHANNELS:
            ceiling = MAX_VOLUME if ch == "volume" else CH_MAX
            acts = [
                {"at": int(t0 + i * DT_MS), "pos": encode_pos(val, ceiling)}
                for i, val in enumerate(decoded[ch])
            ]
            channels[ch] = Funscript(actions=acts)

    if out_dir is not None:
        estim_dir = os.path.join(out_dir, "estim")
        os.makedirs(estim_dir, exist_ok=True)
        for ch, fs in channels.items():
            dump_funscript(fs, os.path.join(estim_dir, f"{name}.{ch}.funscript"))

    return channels
