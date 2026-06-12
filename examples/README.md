# Examples

Drop sample inputs here to try the engine end-to-end — a 1-D stroke `.funscript`
and (optionally) a chapter sidecar JSON.

```
examples/
  <your-clip>.funscript          # 1-D stroke motion (the input)
  <your-clip>.chapters.json      # optional: chapter boundaries (sidecar)
  sample.chapters.json           # an illustrative sidecar (see below)
```

## Run

```bash
# e-stim full channel set
forge-funscript-engine examples/<your-clip>.funscript -o examples/out

# with your chapter sidecar (per-chapter Feel + seam stitching)
forge-funscript-engine examples/<your-clip>.funscript -o examples/out \
    --chapters-file examples/<your-clip>.chapters.json

# single-axis stroker
forge-funscript-engine examples/<your-clip>.funscript -o examples/out --device handy
```

Output lands in `examples/out/<device>/`.

## Chapter sidecar format

The parser is intentionally tolerant so different tools' files fit. A sidecar is
either a top-level array **or** an object with a `chapters` array. Each entry needs
a **start**; the **end** comes from `end`/`duration`, else the next chapter's start,
else the clip end.

- **Times**: a number (or numeric string) = milliseconds (funscript convention);
  a colon string = clock time (`HH:MM:SS.mmm` / `MM:SS`).
- **Start keys** accepted: `start`, `startTime`, `start_ms`, `from`, `begin`, `at`, `time`
- **End keys** accepted: `end`, `endTime`, `end_ms`, `to`, `finish`, `stop`
- **Duration keys**: `duration`, `dur`, `length`
- **Name keys** (optional): `name`, `title`, `label`

See [`sample.chapters.json`](sample.chapters.json) for a concrete example. If your
file doesn't parse, share it and we'll widen the parser.
