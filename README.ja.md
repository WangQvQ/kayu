# KAYU

[English](README.md) · [简体中文](README.zh-CN.md) · **日本語**

好きなものに、小さな居場所を。KAYU（卡屿）は、大切なキャラクターや思い出をデジタルコレクションカードにして、作成・収集・共有できる iPhone アプリです。現在、App Store での初回リリースを準備しています。

[公式サイト](https://wangqvq.github.io/kayu/) · [サポート](https://wangqvq.github.io/kayu/support.html) · [プライバシーポリシー](https://wangqvq.github.io/kayu/privacy.html)

このリポジトリには、英語の公式サイト、オープンソースの **KAYU Card Creator** Agent Skill、個別にダウンロードできるファンアートのカードパックが含まれます。iOS アプリのソースコード、個人のコレクションのバックアップ、サービスの認証情報は公開していません。

## カードパックをダウンロード

[カード一覧とプレビュー](cards/README.ja.md)、または [GitHub Releases](https://github.com/WangQvQ/kayu/releases/tag/card-packs-v1.0.0) をご覧ください。

『呪術廻戦』と『鬼滅の刃』の `.kayu` パックを 4 種類、合計 36 枚用意しています。ファイルをダウンロードして KAYU にインポートすると、まず「Packs」に未開封の状態で保存されます。好きなときに開封してコレクションに追加できます。

## Creator Skill のインストール

`skills/kayu-card-creator` を、お使いの Agent の Skill ディレクトリにコピーしてください。Codex の場合、通常は `~/.codex/skills/kayu-card-creator` です。再起動するか Skill の検出を更新してから、次のように依頼できます。

> $kayu-card-creator を使って、私のイラストを立体的なレイヤー表現のある KAYU カードパックにしてください。

ツールの実行には Python 3.9 以降と Pillow 10.1 以降が必要です。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install 'Pillow>=10.1'
.venv/bin/python skills/kayu-card-creator/scripts/kayu.py --help
```

Agent が利用できる画像生成ツールや、ご自身の画像を使用できます。Seedream は任意の追加機能で、ご自身の認証情報と対応モデルが必要です。Skill をインストールしただけで有料の画像生成リクエストが実行されることはありません。

出力は常に **`.kayu` パック**です。カードが 1 枚の場合もパックにまとめます。iPhone の「ファイル」アプリからインポートし、KAYU の「Packs」で開封してください。

詳しくは [Skill](skills/kayu-card-creator/SKILL.md) と [形式の説明](skills/kayu-card-creator/references/format.md)（英語）をご覧ください。

## ツールの検証

```sh
.venv/bin/python tests/test_creator.py
```

平面カード、レイヤー付きカード、傾きで画像が切り替わるカード、複数枚のパック、破損した素材の拒否、ID の重複、メタデータの長さ制限、既存ファイルの保護をオフラインで確認します。有料の画像生成 API は呼び出しません。

## 公式サイト

`docs/` は GitHub Pages で公開する、実行時の依存関係を持たない静的サイトです。ローカルでのプレビュー：

```sh
python3 -m http.server --directory docs 8080
```

## フィードバック

使い方のご質問やツールの不具合は、[GitHub Issues](https://github.com/WangQvQ/kayu/issues/new/choose) へお寄せください。Issue は公開されるため、API キー、Apple の認証情報、私的な写真、コレクション全体のバックアップは添付しないでください。

コードとドキュメントには [MIT ライセンス](LICENSE) が適用されます。アプリのキャラクターイラスト、ブランド素材、ファンアートのカードパックは対象外です。[素材に関する説明](ASSET-NOTICE.md)をご確認ください。
