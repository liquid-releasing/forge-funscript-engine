"""The `.forge` bundle: a manifest-indexed set of artifacts (FunscriptForge `ffmeta/v1`).

`manifest.ffmeta` (JSON) is the index that ties the loose files together — the
`motion.funscript` plus the chapters/phrases/characters sidecars. This module reads
the manifest, resolves the artifacts relative to it, and returns a `Bundle` the engine
can generate from directly: "point at a `.forge` and render."

This is the keystone for the future `.forge` zip container (docs/forge-container.md):
swap directory resolution for zip member resolution and the rest is unchanged.
"""
import json
import os
from dataclasses import dataclass, field

from .funscript import load_funscript
from .chapters import load_chapters_file
from .assess import load_phrases

MANIFEST_NAME = "manifest.ffmeta"


@dataclass
class Bundle:
    root: str                                   # directory the artifacts resolve against
    stem: str = "out"                           # output basename
    duration_ms: int = 0
    motion_actions: list = field(default_factory=list, repr=False)
    chapters: list = None                       # [(start_ms, end_ms), …] or None
    phrases: list = field(default_factory=list, repr=False)
    paths: dict = field(default_factory=dict)   # analysis/role -> resolved path
    manifest: dict = field(default_factory=dict, repr=False)


def find_artifacts(manifest, **filters):
    """Artifacts whose fields match all `filters` (e.g. kind='sidecar', analysis='chapters')."""
    return [a for a in manifest.get("artifacts", [])
            if all(a.get(k) == v for k, v in filters.items())]


def _first(manifest, **filters):
    hits = find_artifacts(manifest, **filters)
    return hits[0] if hits else None


def _resolve(root, artifact):
    return os.path.join(root, artifact["path"]) if artifact else None


def load_manifest(path):
    """Read a manifest.ffmeta (JSON). `path` may be the manifest file or its directory."""
    if os.path.isdir(path):
        path = os.path.join(path, MANIFEST_NAME)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), os.path.dirname(os.path.abspath(path))


def load_bundle(path):
    """Load a `.forge` bundle (manifest path or its directory) -> Bundle.

    Resolves the stroke motion funscript and the chapters/phrases sidecars. Missing
    sidecars are simply absent (chapters -> None, phrases -> []).
    """
    manifest, root = load_manifest(path)

    motion_art = (_first(manifest, kind="funscript", role="stroke")
                  or _first(manifest, kind="funscript"))
    if motion_art is None:
        raise ValueError("bundle manifest has no funscript artifact")
    motion_path = _resolve(root, motion_art)
    motion_actions = load_funscript(motion_path).actions

    duration_ms = int(manifest.get("duration_ms")
                      or (motion_actions[-1]["at"] if motion_actions else 0))

    chapters = None
    ch_art = _first(manifest, kind="sidecar", analysis="chapters")
    if ch_art is not None:
        chapters = load_chapters_file(_resolve(root, ch_art), clip_end_ms=duration_ms)

    phrases = []
    ph_art = _first(manifest, kind="sidecar", analysis="phrases")
    if ph_art is not None:
        phrases = load_phrases(_resolve(root, ph_art))

    paths = {}
    for a in manifest.get("artifacts", []):
        key = a.get("analysis") or a.get("role")
        if key and key not in paths:
            paths[key] = _resolve(root, a)

    return Bundle(
        root=root,
        stem=manifest.get("stem") or "out",
        duration_ms=duration_ms,
        motion_actions=motion_actions,
        chapters=chapters,
        phrases=phrases,
        paths=paths,
        manifest=manifest,
    )


def generate_from_bundle(path, device="estim", out_dir=None, **kwargs):
    """Load a `.forge` bundle and render it: motion + chapters drive generation, the
    manifest `stem` names the output. Returns {channel: Funscript}.

    Extra kwargs pass through to the generator (full, emit_carrier, enable_rise_time, …).
    """
    from .pipeline import generate_estim, generate_single_axis
    b = load_bundle(path)
    if device == "estim":
        return generate_estim(b.motion_actions, chapters=b.chapters, name=b.stem,
                              out_dir=out_dir, **kwargs)
    return generate_single_axis(b.motion_actions, device=device, name=b.stem,
                               out_dir=out_dir, **kwargs)
