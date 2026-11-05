# Optional Seedream workflow

The bundled optional adapter uses
`https://ark.cn-beijing.volces.com/api/v3/images/generations`. Supply your own
`ARK_API_KEY` and `--model` with a model your provider account supports.
Layer decomposition requires provider/model support; otherwise prepare
layers with the agent's editing or segmentation tools. Do not borrow keys
from another project or ship them in config, packs, screenshots, or logs.

```sh
python "$SKILL_DIR/scripts/kayu.py" generate --idea "A moonlit garden traveler" \
  --model YOUR_COMPATIBLE_MODEL --style original --title "Moonlit Letters" \
  --creator "Your name" --out-dir work/moonlit
python "$SKILL_DIR/scripts/kayu.py" decompose --image work/original.png \
  --model YOUR_COMPATIBLE_MODEL --title "Moonlit Letters" \
  --creator "Your name" --rarity SSR --out-dir work/spatial
```

Generation requests 1584×2400; decomposition requests the provider's 2K
size. Both request `watermark=false`. This does not promise removal of
invisible provenance or another creator's attribution. References are PNG
data URIs, capped at 30 MB for decomposition. No automatic paid retry.
Inspect saved stages before retrying so successful generation is not repeated.

Rebuild from downloaded layers without credentials or paid calls:

```sh
python "$SKILL_DIR/scripts/kayu.py" decompose \
  --manifest work/decomposition.json --layers-dir work/downloaded \
  --title "Moonlit Letters" --creator "Your name" --out-dir work/rebuilt
```

The response manifest has a `data` array. Cache images in array order as
`layer-0.png`, `layer-1.png`, etc. Without a cache, the helper downloads the
response URLs, which may expire. These URLs are never embedded in final packs.
Treat manifests as private work files if they contain signed URLs.

`z_index=0` is the base. Other crops are restored using
`bounding_box.absolute=[left,top,right,bottom]` in base-image pixels, or
`normalized` in **0…1000**, not 0…1. Composite in increasing z-index;
restore the original layout before fitting the group to the card canvas.
If role detection fails, inspect the cache and use `--subject-layer 2`
with the real subject z-index.

Output includes aligned layer PNGs, `card.json`, `card.kayu`, an internal
`card.shancard`, and a preview. Inspect masks, background repair, and actual
occlusion before claiming that the spatial card is finished.
