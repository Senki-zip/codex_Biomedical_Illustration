# Editable SVG scene format

Use a JSON object with `width`, `height`, optional `title`, optional `background` (default white), and arrays `nodes`, `edges`, and `labels`. Units are SVG pixels. A practical figure is 1200 by 700; avoid relying on automatic text wrapping.

Each node has a unique `id`, `x`, `y`, `width`, `height`, and optional `label`, `label_size`, `label_color`, `label_offset`, `fill`, `stroke`. Set `asset` to an ID returned by search to embed an icon. Without an asset, `shape` can be `rect` (default) or `ellipse`; `radius` controls rectangle corners. `label_position: inside` places a label at the center, otherwise it is below the node. `note` is an optional small second label below. A `panel: true` node is rendered behind edges and other nodes, useful for cell compartments.

Each edge has `from`, `to` (node IDs), `kind` (`activation`, `inhibition`, `binding`), optional `color`, `width`, `dashed`, and `label`. `from_anchor` and `to_anchor` can be `top`, `bottom`, `left`, `right`, or `center`; defaults choose facing edges. To route around objects, provide `points: [[x,y], ...]` including endpoints. `label_x` and `label_y` can override the midpoint label position. Edges render behind ordinary nodes. Hypothetical relations use `dashed: true` and a clear legend.

`labels` entries contain `text`, `x`, `y`, and optional `size`, `color`, `weight`, `anchor` (`start`, `middle`, `end`). The optional title is placed at x=32, y=43; leave space above nodes. Text uses the local sans-serif stack with CJK fallbacks; fonts are not embedded. Check Chinese glyphs in the chosen renderer.

```json
{
  "width": 1000, "height": 440, "title": "Illustrative mechanism — example only",
  "nodes": [
    {"id":"a", "x":60,"y":150,"width":160,"height":80,"label":"Stimulus","label_position":"inside","fill":"#e0f2fe"},
    {"id":"b", "x":420,"y":150,"width":160,"height":80,"label":"Regulator","label_position":"inside","fill":"#dcfce7"},
    {"id":"c", "x":780,"y":150,"width":160,"height":80,"label":"Output","label_position":"inside","fill":"#fef3c7"}
  ],
  "edges": [
    {"from":"a","to":"b","kind":"activation","label":"activates"},
    {"from":"b","to":"c","kind":"inhibition","dashed":true,"label":"proposed inhibition"}
  ]
}
```

Get actual asset IDs from search rather than inventing them. The compositor does not recolor source artwork; change a copied SVG explicitly when needed and record that modification in the attribution. Composition itself records resizing and placement. After changing the scene, rerun compose; the SVG contains self-contained artwork rather than file links.
