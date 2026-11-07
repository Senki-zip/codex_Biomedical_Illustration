---
name: bio-mechanism
description: Search downloaded scientific SVG artwork in Chinese or English, preview and export assets for BioRender, and compose editable biological mechanism diagrams with source and license records. Use for biological illustrations, cell or signaling mechanisms, and requests for local free science icons. Do not use for statistical charts or imply access to the user's BioRender account.
---

# 科研机制图素材库

This skill ships with offline BioIcons and Reactome SVG libraries, original license texts and designer/publisher attribution. Source status is recorded in `assets/library/sources.json`; distinguish downloaded assets from external reference links. Run `stats` for current per-source and deduplicated usable counts.

Resolve all script paths relative to this `SKILL.md`, including when the plugin is installed in a cache. The core tool needs Python 3.9+ and only the standard library. Never run the upstream website or install its JavaScript dependencies to use the artwork.

## Find and inspect artwork

```bash
python3 <skill-dir>/scripts/bioassets.py stats
python3 <skill-dir>/scripts/bioassets.py search '细胞核 DNA 转录' --limit 16 --gallery <output-dir>/candidates.html
python3 <skill-dir>/scripts/bioassets.py search 'receptor' --author Servier --limit 12 --json
python3 <skill-dir>/scripts/bioassets.py search '蛋白 受体' --source Reactome --limit 12
```

Chinese terms expand to related English asset names; search results are candidates, not a claim of exact biological identity. For a precise molecule, visually inspect the source SVG or a rendered contact sheet before assigning that label. Prefer consistent authors/styles in a single panel. Use `--license cc-0` to restrict to CC0 when requested; do not call every icon public domain.

The generated HTML gallery is self-contained. Open it or render candidate SVGs with an available local SVG renderer. Search `--limit 0` returns all matches. `stats --verify` checks every original asset against its recorded SHA-256 and parses usable SVGs; known malformed upstream SVGs are reported separately and excluded from search/export/composition.

Byte-identical artwork is shown once in ordinary search. Duplicate IDs remain exportable with their own provenance and license records. `--source BioIcons` and `--source Reactome` restrict results to that source; designer names can differ from the library publisher.

## Export for BioRender

```bash
python3 <skill-dir>/scripts/bioassets.py export <asset-id> <asset-id> --out <output-dir>/materials
```

This copies original SVGs, used license texts, metadata and `ATTRIBUTION.md`. BioRender accepts SVG/PNG/JPG through Uploads; importing an SVG does not guarantee its paths become separately editable in BioRender. This workflow does not provide a BioRender subscription, publishing license or account connector.

## Assemble a mechanism diagram

Translate the user's mechanism into a JSON scene; read [the scene format](references/scene-format.md) when composing a figure. Nodes can contain artwork or editable shapes. Edges support activation arrows, inhibition bars, binding lines and dashed hypothetical links. Layout stays explicit so Codex can refine individual positions.

```bash
python3 <skill-dir>/scripts/bioassets.py compose --spec <scene.json> --out <output-dir>/mechanism.svg
```

Outputs include a standalone SVG with embedded vector paths, a scene JSON copy, an asset manifest, attribution and the applicable license texts. No network or remote fonts are needed. Render and inspect the result with an available SVG renderer before delivery. The original SVG remains editable even if a PNG preview is also provided.

An optional PNG preview helper uses `sharp` from the installed Codex dependency runtime, or from normal Node resolution:

```bash
node <skill-dir>/scripts/render.cjs <output-dir>/mechanism.svg <output-dir>/mechanism.png 1800
```

Use only relations supplied by the user or supported by the requested evidence. Show proposed mechanisms as proposed, and distinguish binding, activation and inhibition. Do not substitute a nearby biological object silently. Keep generic demonstrations labelled as examples.

For asset origin, license handling and optional libraries, consult [sources](references/sources.md). Preserve each downloaded version's license; a current website license does not automatically relabel an older snapshot.

## Update downloaded sources

When the user asks to update or expand the library, run the relevant command from the writable plugin source directory, then validate and reinstall the updated plugin. Updates require internet access; ordinary search and drawing remain offline.

```bash
python3 <skill-dir>/scripts/sync_library.py bioicons
python3 <skill-dir>/scripts/sync_library.py reactome --workers 4
python3 <skill-dir>/scripts/bioassets.py stats --verify
```

BioIcons updates compare upstream Git blob hashes and preserve established IDs. Reactome uses the complete public icon catalog and individual SVG URLs; cached files are reused on interrupted downloads. Use `--refresh` to re-fetch existing Reactome SVGs when refreshing artwork content. Failed downloads are explicitly reported, never counted as installed. Avoid running two sync commands against the same writable library concurrently. The optional `requests` package speeds up connection reuse; standard-library downloading is available without it.
