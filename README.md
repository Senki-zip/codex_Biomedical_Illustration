# Biomedical Illustration

A local Codex plugin with an open scientific SVG library, English and Chinese search, asset previews, BioRender import bundles, and editable biological mechanism diagrams.

![Generic mechanism example](docs/example.png)

The example demonstrates the plugin's illustration features.

## Features

- Search cells, organelles, DNA, proteins, receptors, and laboratory equipment offline.
- Generate self-contained HTML galleries.
- Export original SVGs with authors, source records, attribution, and applicable license texts.
- Compose editable SVG scenes with activation arrows, inhibition bars, association lines, and dashed relationships.
- Generate optional PNG previews. Core tools require Python 3.9+ and its standard library.

## Install in Codex

```bash
codex plugin marketplace add Senki-zip/codex_Biomedical_Illustration
codex plugin add bio-mechanism@biomedical-illustration
```

Open a new conversation after installation. Restart Codex if the skills have not appeared. You can ask the plugin to find nucleus, DNA, and protein artwork, show candidate previews, and assemble an editable diagram from your mechanism description.

You can also clone the repository and register its local marketplace.

```bash
git clone https://github.com/Senki-zip/codex_Biomedical_Illustration.git
codex plugin marketplace add ./codex_Biomedical_Illustration
codex plugin add bio-mechanism@biomedical-illustration
```

The repository includes approximately 481.5 MB of indexed original SVGs, which are downloaded during the first installation. The plugin manifest is `plugins/bio-mechanism/plugin.json`. The drawing skill is `plugins/bio-mechanism/skills/bio-mechanism/SKILL.md`.

## Use the skills

The plugin includes two callable skills.

| Skill | Purpose | Example prompt |
| --- | --- | --- |
| [`bio-mechanism-guide`](plugins/bio-mechanism/skills/bio-mechanism-guide/SKILL.md) | Usage instructions, library checks, and onboarding | `Use $bio-mechanism-guide to teach me how to create a mechanism diagram.` |
| [`bio-mechanism`](plugins/bio-mechanism/skills/bio-mechanism/SKILL.md) | Asset search, previews, exports, and diagram composition | `Use $bio-mechanism to find DNA, nucleus, and protein artwork and create a candidate gallery.` |

Type `$` in Codex to find loaded skills, or describe your task in natural language for automatic selection. The guide is also the plugin's onboarding skill and can be opened from the setup entry point in supporting clients.

```text
Use $bio-mechanism-guide to check the local library and explain the workflow.

Use $bio-mechanism to find six CC0 cell and nucleic-acid icons and export the SVGs with source and attribution records for BioRender.

Use $bio-mechanism to draw this mechanism. A activates B, B inhibits C, and the relationship from B to D is proposed. Provide editable SVG, a PNG preview, and artwork attribution.
```

Include the main molecules, their cell or organelle locations, activation and inhibition relationships, proposed relationships, and layout preferences when requesting a diagram.

## Command-line usage

Run these commands from the cloned repository root.

```bash
BIO_SKILL_DIR="./plugins/bio-mechanism/skills/bio-mechanism"

# Search and generate a candidate gallery
python3 "$BIO_SKILL_DIR/scripts/bioassets.py" search 'nucleus DNA receptor' --limit 16 --gallery ./candidates.html

# Filter by author or license
python3 "$BIO_SKILL_DIR/scripts/bioassets.py" search receptor --author Servier --limit 12
python3 "$BIO_SKILL_DIR/scripts/bioassets.py" search DNA --license cc-0 --limit 12

# Export original SVGs and attribution
python3 "$BIO_SKILL_DIR/scripts/bioassets.py" export bio-94be01feee5b bio-1161c95976be --out ./materials

# Compose an editable SVG example
python3 "$BIO_SKILL_DIR/scripts/bioassets.py" compose --spec "$BIO_SKILL_DIR/assets/examples/generic-mechanism.scene.json" --out ./mechanism.svg

# Verify asset integrity
python3 "$BIO_SKILL_DIR/scripts/bioassets.py" stats --verify
```

The scene schema is documented in [scene-format.md](plugins/bio-mechanism/skills/bio-mechanism/references/scene-format.md). PNG previews require Node.js and the optional `sharp` package, loaded through normal Node resolution or the bundled Codex runtime.

```bash
node "$BIO_SKILL_DIR/scripts/render.cjs" ./mechanism.svg ./mechanism.png 1800
```

## Library coverage and quality

Artwork comes from BioIcons and the Reactome Icon Library. The BioIcons main branch was checked on November 7, 2026 and still points to `d29e766ea7580b8063c4f47b29e872db40a4d979`. All 2,571 Reactome catalog SVGs were imported with designer and source metadata. BioIcons includes contributions from Servier, DBCLS, and other authors. [BioIcons](https://github.com/duerrsimon/bioicons), [Reactome](https://reactome.org/icon-lib)

| Measure | Count |
| --- | ---: |
| Original SVG files retained | 5,401 |
| Indexed asset records | 5,400 |
| Unique SVGs available in ordinary search | 5,393 |
| Byte-identical duplicate records with retained IDs and provenance | 3 |
| Malformed upstream SVGs retained and excluded from use | 4 |
| Unindexed SVG with a missing author directory | 1 |

The index is built from actual files and records each asset's author, license, source URL, and SHA-256. Initial validation is recorded in [validation.json](docs/validation.json), with the expanded library audit in [library-update-2026-11-07.json](docs/library-update-2026-11-07.json). NIH BioArt is listed as an external reference source. Download status is recorded in [sources.json](plugins/bio-mechanism/skills/bio-mechanism/assets/library/sources.json).

Original third-party SVGs and upstream catalogs retain their source-language editor metadata, names, and provenance fields for byte-level verification. Repository documentation, plugin interfaces, generated galleries, and example prompts are in English. Search supports Chinese aliases through Unicode-escaped data in the implementation.

## Update and expand the library

Version 1.1.0 introduced multiple-source updates, source filtering, content deduplication, and independent license notices. Version 1.1.1 provides English repository documentation and interfaces.

```bash
BIO_SKILL_DIR="./plugins/bio-mechanism/skills/bio-mechanism"

# Check the latest BioIcons commit and download files whose Git hashes changed
python3 "$BIO_SKILL_DIR/scripts/sync_library.py" bioicons

# Import the complete Reactome catalog and reuse cached files after interruptions
python3 "$BIO_SKILL_DIR/scripts/sync_library.py" reactome --workers 4

# Re-fetch existing Reactome artwork when refreshing content
python3 "$BIO_SKILL_DIR/scripts/sync_library.py" reactome --refresh --workers 4

# Filter by source and verify integrity
python3 "$BIO_SKILL_DIR/scripts/bioassets.py" search 'protein receptor' --source Reactome --limit 12
python3 "$BIO_SKILL_DIR/scripts/bioassets.py" stats --verify
```

Search and drawing work offline. Updates access the relevant public sources. The optional `requests` package improves connection reuse, with standard-library downloading as the fallback. Run updates sequentially for each writable library.

Deduplication uses the original file's SHA-256. Duplicate IDs remain exportable with their own source and license records. Updating one source preserves other source catalogs. Reactome coverage and download failures are recorded explicitly, with successful downloads included in installed counts.

The expansion audit and sample artwork are available in the [update record](docs/library-update-2026-11-07.md) and [Reactome preview](docs/reactome-preview.png).

## Use assets in BioRender

Upload exported SVGs through BioRender's Uploads panel. Keep the accompanying `ATTRIBUTION.md`, `assets.json`, and `licenses/` files. Editing individual paths depends on BioRender's import behavior. BioRender account connections, proprietary assets, and subscription features are managed separately in BioRender.

## Licensing and attribution

Plugin code and documentation use the MIT License. Each artwork retains its upstream license. [Plugin license](LICENSE)

Artwork licenses include CC0, CC BY 3.0/4.0, CC BY-SA 3.0/4.0, MIT, and BSD. Follow each entry's attribution, modification, notice, and other license requirements. License texts are bundled with the artwork, and per-asset records are available in the [index](plugins/bio-mechanism/skills/bio-mechanism/assets/library/index.json).

Some Servier artwork in this BioIcons snapshot uses CC BY 3.0. Snapshot-specific license records govern those copies. Attribution for the example artwork is included in [example-sources](docs/example-sources/ATTRIBUTION.md).

## Upstream resources

- [BioIcons](https://bioicons.com/)
- [Servier Medical Art](https://smart.servier.com/)
- [Reactome Icon Library](https://reactome.org/icon-lib)
- [DBCLS TogoTV](https://togotv.dbcls.jp/en/pics.html)
- [Codex plugin packaging documentation](https://developers.openai.com/plugins/build/plugins)
