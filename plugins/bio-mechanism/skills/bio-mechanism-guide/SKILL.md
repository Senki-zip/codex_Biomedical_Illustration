---
name: bio-mechanism-guide
description: Explain how to use the Biomedical Illustration plugin and its skills, check the installed local artwork library, and guide users through finding SVG assets, exporting a BioRender import bundle, or composing a first mechanism diagram. Use for onboarding, usage instructions, and getting-started requests.
---

# Biomedical Illustration Usage Guide

Explain the plugin in the user's language and give a directly actionable next step based on their goal. When the user has supplied a drawing task, proceed to the relevant workflow.

## Locate the installed plugin

This file's directory is `<guide-dir>`. The sibling drawing skill directory `../bio-mechanism/` is `<draw-dir>`. Resolve paths relative to this skill file so they work in an installation cache.

Read the [drawing skill](../bio-mechanism/SKILL.md), then run the library statistics command.

```bash
python3 <draw-dir>/scripts/bioassets.py stats
```

Use the actual output when describing asset counts and download status. Distinguish indexed records, original files, and unique usable SVGs. Run `stats` for onboarding, and use `stats --verify` when the user requests an integrity audit or encounters damaged artwork.

## Explain the two skills

- `$bio-mechanism-guide` provides usage instructions, library checks, and first-use guidance.
- `$bio-mechanism` performs asset search, previews, exports, and editable SVG mechanism composition.

Users can also describe a task in natural language for automatic skill selection.

> Use the scientific artwork library to find nucleus, DNA, protein, and membrane receptor assets and generate a candidate gallery.

> Use $bio-mechanism to find six CC0 scientific icons and export SVGs with source records for BioRender.

> Use $bio-mechanism to illustrate these relationships. A activates B, B inhibits C, and the link from B to D is proposed. Provide SVG, a PNG preview, and attribution.

## Guide the requested workflow

**Find artwork.** Translate the requested objects into suitable search terms. Run `bioassets.py search` with `--gallery` to generate a candidate gallery. Retain the actual asset IDs returned by search. Use `--author` for visual consistency or `--license cc-0` when requested.

**Import into BioRender.** Select actual asset IDs and run `bioassets.py export`. Provide SVGs, `ATTRIBUTION.md`, `assets.json`, and the applicable license files. Explain uploading through BioRender's Uploads panel. BioRender account and subscription features are managed in BioRender. Individual-path editing depends on its SVG import behavior.

**Draw a mechanism.** Build a JSON scene from the supplied molecular relationships and layout preferences, then run `compose` using the [scene format](../bio-mechanism/references/scene-format.md). For an explicitly requested demonstration, use `<draw-dir>/assets/examples/generic-mechanism.scene.json` and label it as a generic example. Render with `render.cjs`, inspect the preview, and deliver SVG, scene JSON, and attribution. If the optional renderer is unavailable, deliver the SVG and explain that the PNG remains pending.

For usage questions, give a concise workflow and example prompts. If a requested drawing lacks mechanism details, ask for the main molecules, activation or inhibition relationships, and intended use while searching for objects already specified.

## Common tasks and troubleshooting

- **Update or expand the library.** Follow the drawing skill's update instructions to run `sync_library.py bioicons` or `sync_library.py reactome`, then check statistics and integrity. Filter using `--source BioIcons` or `--source Reactome`. Usable totals are deduplicated by content hash, while duplicate IDs and provenance remain accessible.
- **Find an installed skill.** Open a new conversation, then restart Codex if needed. Use `codex plugin list` to inspect installation and enabled status.
- **Improve search results.** Try English terms, synonyms, and broader categories. Verify the visual identity of a generic icon before assigning a specific molecule's name.
- **Revise a diagram.** Update objects, labels, and connections in the scene JSON and regenerate the SVG. Preserve source records and document modifications when recoloring artwork.
- **Prepare publication attribution.** Use the exported per-asset records and comply with each artwork's own license.

Source details are in [sources.md](../bio-mechanism/references/sources.md). The repository README documents installation and layout. This skill must also work independently within the plugin installation cache.
