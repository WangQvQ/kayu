---
name: kayu-card-creator
description: Create digital keepsake card packs for the KAYU iPhone app using existing illustrations, AI artwork, registered transparent layers, and optional themed frames. Package and validate .kayu files; not for study flashcards.
---

# KAYU Card Creator

Deliver an importable keepsake, not just a mockup. This Skill is self-contained;
no app checkout, model subscription, or shared API key is included.

## Choose the artwork route

Start with the user's illustration or idea. Preserve their chosen character,
face, outfit, and style. Infer ordinary creative choices from the request.
Use the agent's available image generation/editing tools when appropriate;
use existing assets directly when the user wants to keep them.

- **One illustration:** make a flat card, or separate its subject and reconstruct
  a clean background for spatial depth. A redrawn character is not a faithful layer.
- **Existing layers:** check common canvas registration and real alpha, then package.
- **Two-image lenticular:** use complete `imageA` and `imageB` faces that switch with tilt.

Read [art direction](references/art-direction.md) for composition and prompting,
[format](references/format.md) when building a config, and
[Seedream](references/seedream.md) only for that optional provider route.

## Preserve these invariants

- Output canvas: **1320×2000 (66:100)**, same front/back ratio. An image generator
  may use 1584×2400; the helper fits assets proportionally, without stretching.
- Spatial cards require a complete, opaque background without a duplicate
  character and a genuinely transparent subject PNG. Register subject, effects,
  and frame on the original canvas before scaling the group. Restore cropped
  layers using their bounding boxes; never stretch each crop over the whole card.
- Frames and typeset lettering become the fixed `text` layer. Keep faces, hands,
  and held objects clear. Supply a font with the needed glyphs when printing titles.
  SSR/UR are chosen visual labels, not scarcity claims or random-draw odds.
- Images: at most 4096×4096; 40 MB decoded resources per card. Packs: 1–60 unique
  cards, 160 MB decoded resources, 240 MB encoded file. Aim much smaller for sharing.
- Deliver **`.kayu`**, even for one card. `.shancard` is an internal intermediate
  used by this helper and is not an import format for the current app.
- Never include credentials, absolute source paths, signed download URLs, or
  request logs in delivered packs. Use only credentials supplied for this task.
  Do not remove another creator's attribution from supplied artwork.

## Build and inspect

Requires Python 3.9+ and Pillow 10.1+. Install dependencies in a working virtual
environment when needed; do not include that environment in a shared Skill.
Set `SKILL_DIR` to this folder. Config asset paths are relative to the config.

```sh
python "$SKILL_DIR/scripts/kayu.py" make work/card.json --out work/card.shancard
python "$SKILL_DIR/scripts/kayu.py" validate work/card.shancard
python "$SKILL_DIR/scripts/kayu.py" pack work/card.shancard \
  --title "Moonlit Letters" --creator "Your name" --out work/moonlit.kayu
python "$SKILL_DIR/scripts/kayu.py" validate work/moonlit.kayu
```

`make` also writes `.preview.png`. Inspect it and the actual layer sources:
intact anatomy, correct glyphs, aligned layers, clean transparent edges,
no duplicate subject in the background, restrained effects. Structural
validation cannot prove visual quality or a convincing depth effect.

For multiple cards, pass their intermediate files to `pack`. Each revised
work needs a new card ID; duplicate IDs intentionally do not overwrite old cards.
Deliver the `.kayu` pack and preview, plus source layers/config if requested.
Do not publish, upload, or message the work unless the user requests it.

Explain import: download the entire file into iPhone Files, open it with KAYU
or choose local file import in Packs. It arrives **unopened**; the user unwraps
it before adding it to a collection. Import works offline once downloaded.
When an app/test device is available, verify that flow and tilt/flip behavior.
Otherwise state that the file passed structural checks and device import
has not been verified; do not invent an acceptance result.

## Optional generation workflow

The helper's `generate`/`decompose` commands use Seedream HTTPS with the user's
own `ARK_API_KEY` and a compatible `--model`. Read the provider reference first.
A generation runs at most one image request and one decomposition request;
no automatic paid retries. Preserve completed output on failure. If splitting
fails after generation, retry decomposition of the saved original rather than
paying to generate the same image again. Do not silently deliver a flat card
while claiming spatial layers are complete.
