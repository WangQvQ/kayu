# Art direction and prompts

Combine character/reference constraints, action and scene, palette and mood,
card treatment, separation needs, and safe areas. These are examples, not a
mandatory anime style: follow the user's chosen artwork.

> Vertical 66:100 keepsake illustration, one character, coherent subject and
> environment lighting. Preserve the reference face, hair, outfit, and visual
> style. Keep hair, hands, and held objects intact with a safe edge margin.
> [Scene], [palette], [mood]. [Borderless art / themed fantasy frame / technical
> dossier]. Clearly separable background, character, frame, and foreground.
> No text, rarity labels, serial numbers, or pseudo-watermark lettering;
> typeset them later. [User's additional direction].

Drop reference-preservation constraints when there is no reference. Writing
“3D” or “depth of field” affects illustration style; it does not produce
independently movable layers.

For decomposition:

> Complete scene without the character as the opaque background. Character,
> hair, clothing, and held objects together as the subject. Frame, foreground,
> and effects as separate transparent layers. Preserve the exact original
> composition and placement. No character ghost, holes, or new objects.
> Give layers explicit role names.

Inspect subject/background before adding foil. A background repair layer
whose name mentions “no character” must not be mistaken for the subject.
When automatic role detection is ambiguous, inspect and assign the actual
subject with `--subject-layer`.

A series can share palette, lettering, frames, and backs. Keep particles
restrained; do not use them to conceal bad masks. Decorative rarity labels
and borders must leave the illustration readable.
