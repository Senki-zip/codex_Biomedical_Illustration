# Artwork sources and provenance

## Downloaded BioIcons snapshot

- Repository: https://github.com/duerrsimon/bioicons
- Pinned commit: `d29e766ea7580b8063c4f47b29e872db40a4d979`
- Individual artwork: `assets/library/bioicons/icons/<license>/<category>/<author>/<name>.svg`
- Metadata: `assets/library/index.json`, original `icons.json` and `authors.json`.
- License texts: each license directory's original `LICENSE`.
- The upstream repository's MIT license describes its code; it does not replace individual artwork licenses. This snapshot includes CC0, CC BY 3.0/4.0, CC BY-SA 3.0/4.0, MIT and BSD artwork.
- Retain attribution, source link, license link, and indicate changes when required. Keep complete notices for MIT/BSD. BY-SA icons retain their own terms; do not describe them as unrestricted or silently relicense the artwork or an adapted asset.

The library includes many Servier and DBCLS illustrations. Preserve their snapshot-specific per-icon licenses; the current Servier site advertises CC BY 4.0, while older BioIcons copies may be CC BY 3.0.

## Other sources

- Servier official PowerPoint kits: https://smart.servier.com/image-kits-by-category/ — current CC BY 4.0. If a kit archive is present under `assets/library/servier/`, `sources.json` records its actual download status and hash. These archives are supplementary source documents, not separately indexed SVGs.
- NIH BioArt: https://bioart.niaid.nih.gov/ — per-entry Public Domain or stated license, https://bioart.niaid.nih.gov/faqs . No blanket relicensing or claim that all entries are public domain.
- Reactome Icon Library: https://reactome.org/icon-lib — CC BY 4.0 on the library page. The library is imported through its public icon search catalog and individual SVG download URLs rather than relying on the unavailable bulk archive. Original designer names, designer URLs, icon IDs, descriptions and full upstream catalog are preserved under `assets/library/reactome/`. Retain the additional Reactome publisher attribution to CSHL, OICR and EMBL-EBI, including the exported `NOTICE` file. `sources.json` and `reactome/update-report.json` record actual downloaded counts and any failures.

## Updates and deduplication

`scripts/sync_library.py bioicons` checks the latest main commit and compares per-file Git hashes before downloading changes. The pinned source URL in each resulting entry records the actual commit. See `bioicons/update-report.json` for the latest check; `snapshot.json` retains the initial archive import record.

`scripts/sync_library.py reactome` uses the complete icon catalog and caches downloaded SVGs. `--refresh` fetches existing artwork again. The tool validates complete catalog coverage before merging, records download failures, and retains other libraries when updating one source. The legacy archive importer also preserves other source records.

The merged `index.json` retains all source IDs. Exact SHA-256 duplicates have `duplicate_of` pointing to the canonical ID and are excluded from ordinary search totals; they remain exportable with their individual license and attribution. This is byte-level deduplication, not a claim that visually similar artwork is identical. Source catalogs are also saved under `assets/library/catalogs/`.

Local commands need no account, API key, subscription, or paid generation service. External source lookup and downloading additional artwork require internet access. These are original open artwork libraries, not BioRender's proprietary icon library.
