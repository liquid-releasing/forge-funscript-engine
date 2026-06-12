"""Funscript I/O. Funscript is a render target, not the working format (spec section 4)."""
import json
from dataclasses import dataclass, field


@dataclass
class Funscript:
    actions: list = field(default_factory=list)  # [{"at": int ms, "pos": int 0..100}]
    inverted: bool = False
    range: int = 100
    version: str = "1.0"

    @property
    def is_empty(self) -> bool:
        return len(self.actions) == 0


def load_funscript(path) -> Funscript:
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    return Funscript(
        actions=doc.get("actions", []) or [],
        inverted=bool(doc.get("inverted", False)),
        range=int(doc.get("range", 100)),
        version=str(doc.get("version", "1.0")),
    )


def dump_funscript(fs: Funscript, path) -> None:
    doc = {
        "version": fs.version,
        "inverted": fs.inverted,
        "range": fs.range,
        "actions": fs.actions,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
