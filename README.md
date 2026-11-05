# KAYU

**English** · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)

A little home for the things you love. KAYU (卡屿) is an iPhone app for making,
collecting, and sharing digital keepsake cards. Its App Store release is being prepared.

[Website](https://wangqvq.github.io/kayu/) ·
[Support](https://wangqvq.github.io/kayu/support.html) ·
[Privacy](https://wangqvq.github.io/kayu/privacy.html)

This public repository contains the English website and the **KAYU Card Creator**
agent Skill. The iOS application source, private collection backups and credentials are not included.

## Card pack downloads

[Browse the card packs](cards/README.md) for Jujutsu Kaisen and Demon Slayer.
Download `.kayu` files from the [card pack release](https://github.com/WangQvQ/kayu/releases/tag/card-packs-v1.0.0), import into Packs, and unwrap them in KAYU.

## Install the creator Skill

Copy `skills/kayu-card-creator` into your agent's skills directory. For Codex,
that is normally `~/.codex/skills/kayu-card-creator`. Restart or refresh your
agent's skill discovery, then ask:

> Use $kayu-card-creator to turn my illustration into a layered KAYU card pack.

The portable helper requires Python 3.9+ and Pillow 10.1+:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install 'Pillow>=10.1'
.venv/bin/python skills/kayu-card-creator/scripts/kayu.py --help
```

Use your agent's available image tools or your own artwork. Seedream is an
optional provider workflow and requires your own credentials and compatible
model access. No paid request runs merely by installing the Skill.

The deliverable is always a **`.kayu` pack**, including for a single card.
Import it from the iPhone Files app; it appears in Packs, unopened, ready to unwrap.
See [the Skill](skills/kayu-card-creator/SKILL.md) and
[format reference](skills/kayu-card-creator/references/format.md).

## Verify the helper

```sh
.venv/bin/python tests/test_creator.py
```

This checks flat, layered, and lenticular creation, multi-card packs, corrupt
resource rejection, duplicate IDs, metadata limits, and output preservation.
It does not call a paid image API.

## Website

`docs/` is a dependency-free static site published with GitHub Pages. Preview
locally with `python3 -m http.server --directory docs 8080`.

## Feedback

[Open an issue](https://github.com/WangQvQ/kayu/issues/new/choose) for support
or a tooling bug. Issues are public: never attach API keys, Apple credentials,
private photos, or full collection backups.

Code and documentation: [MIT](LICENSE). App artwork and branding:
[asset notice](ASSET-NOTICE.md).
