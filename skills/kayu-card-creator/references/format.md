# Authoring configuration and portable format

Create a UTF-8 `card.json`. Asset paths are relative to that config:

```json
{
  "title": "Moonlit Letters",
  "creator": "Your name",
  "series": "Night Garden",
  "rarity": "SSR",
  "finish": 3,
  "assets": {
    "background": "background.png",
    "subject": "subject.png",
    "frame": "frame.png",
    "foreground": "foreground.png",
    "back": "back.png"
  }
}
```

Only `title` and usable assets are required. `rarity`: `自制` (self-made,
default), `SR`, `SSR`, or `UR`. Optional `frame`, `foreground`, and `back` may
be omitted; a solid back is supplied. Background and all spatial layers must
already have matching, registered canvases. Back art is fitted separately.
Other roles: `midground`, `effects`, `lineart`, `text`.

For a flat card, use `assets.artwork`. `fit`: `contain` (default, preserves the
whole image) or `fill` (crops edges). For two-image tilt switching, use
`assets.imageA` plus `assets.imageB`. Do not fake layers from a single image.

`showRarity` prints the chosen label (default: on except for `自制`).
`printTitle: true` prints the title and requires a `font` path supporting all
characters. The default stores title as metadata only. Inspect actual glyphs.

`finish`: 0 holographic, 1 gold foil, 2 pearlescent, 3 uncoated (default),
4 matte, 5 silver foil, 6 gloss, 7 spot UV, 8 emboss, 9 deboss, 10 raised UV.
Parameters: `foil`, `particles`, `glow`, `subjectDepth`, `backgroundDepth`,
`effectsDepth`, `starsEnabled`, and `glowEnabled`. The helper bounds overrides;
the app remains the final authority. Stars/glow default to off.

New works get new IDs. Only reuse an explicit `id` for the same immutable
work: a repeat import does not overwrite an existing card.

## Internal intermediate

`.shancard` is UTF-8 JSON used by this helper, not a current app import format,
ZIP, HTML, or renamed picture. Envelope:

```json
{
  "format": "app.shancard.card",
  "version": 1,
  "card": {
    "id": "unique-work-id", "title": "Moonlit Letters", "subtitle": "",
    "creator": "Your name", "story": "", "series": "Night Garden",
    "number": "", "rarity": "SSR", "kind": "holographic", "accent": "B6A3FF",
    "tags": [], "assets": {"background": "embedded", "subject": "embedded"},
    "parameters": {"foil": 0.25, "particles": 0, "glow": 0,
      "starsEnabled": false, "glowEnabled": false},
    "finish": 3, "borderless": true
  },
  "resources": {"background": "BASE64_IMAGE_BYTES", "subject": "BASE64_IMAGE_BYTES"}
}
```

Resource keys must exactly match asset roles. Use standard Base64 bytes,
without a `data:image/…` prefix. Subject alpha must be genuine and nonempty;
background opaque; canvases aligned. `frame` is an authoring convenience
merged into `text`. The helper does not invent a native `photoDesign` recipe.
Images are at most 4096×4096, total 40 MB; encoded intermediate at most 60 MB.

## Deliverable pack

Always call `pack` to create `.kayu`, including for one card. It uses
`format: app.shancard.pack`, `version: 1`; the stable internal format name
is independent of the public extension. The JSON holds 1–60 unique `cards`,
whose asset references are SHA256 hashes, and a top-level `resources` map
of hash to Base64 bytes. Resources are deduplicated. `createdAt` is seconds
since 2001-01-01 UTC (Swift Date encoding), not Unix seconds or ISO text.
Pack title: 1–60 characters; creator: 1–100; message: at most 300.
Total resources: 160 MB; encoded file: 240 MB.

The pack is received unopened. Unwrapping adds its cards to a collection;
single-card and multi-card packs follow the same path. Use the helper rather
than manually writing hashes and timestamps.
