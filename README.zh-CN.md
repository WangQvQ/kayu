# KAYU · 卡屿

[English](README.md) · **简体中文** · [日本語](README.ja.md)

给喜欢的事物一个小小的家。卡屿是一款 iPhone 数字收藏卡 App，用来制作、收藏和分享你珍视的角色与回忆。目前正在准备 App Store 首发。

[官网](https://wangqvq.github.io/kayu/) · [使用支持](https://wangqvq.github.io/kayu/support.html) · [隐私政策](https://wangqvq.github.io/kayu/privacy.html)

本仓库包含英文官网、开源 **KAYU Card Creator** Agent Skill，以及单独下载的同人卡包。iOS App 源代码、私人收藏备份和服务密钥不在公开仓库中。

## 下载卡包

[查看卡包目录与预览](cards/README.zh-CN.md)，或前往 [GitHub Releases 下载](https://github.com/WangQvQ/kayu/releases/tag/card-packs-v1.0.0)。

提供咒术回战与鬼灭之刃 4 个 `.kayu` 卡包，共 36 张卡。下载文件后，在卡屿中从本地导入；卡包会先进入「卡包」的未拆封列表，等你亲手拆开。

## 安装创作 Skill

把 `skills/kayu-card-creator` 复制到 Agent 的技能目录。Codex 通常使用 `~/.codex/skills/kayu-card-creator`。重启或刷新技能发现后，可以这样说：

> 使用 $kayu-card-creator，把我的插画制作成有立体分层效果的卡屿卡包。

便携工具需要 Python 3.9+ 和 Pillow 10.1+：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install 'Pillow>=10.1'
.venv/bin/python skills/kayu-card-creator/scripts/kayu.py --help
```

使用 Agent 已有的生图工具，或你自己的素材。Seedream 是可选流程，需要自行配置凭证与兼容模型；仅安装 Skill 不会发起付费生图请求。

交付格式始终是 **`.kayu` 卡包**，一张卡也封装成卡包。导入后，在「卡包」中拆封，再收进收藏。

详见 [Skill](skills/kayu-card-creator/SKILL.md) 和 [格式说明](skills/kayu-card-creator/references/format.md)（英文）。

## 校验工具

```sh
.venv/bin/python tests/test_creator.py
```

离线检查平面卡、分层卡、双图光栅卡、多卡卡包、损坏资源拒绝、重复 ID、资料长度限制和输出文件保护。不会调用付费生图接口。

## 官网

`docs/` 是通过 GitHub Pages 发布的静态网站，没有运行时依赖。本地预览：

```sh
python3 -m http.server --directory docs 8080
```

## 反馈

通过 [GitHub Issues](https://github.com/WangQvQ/kayu/issues/new/choose) 反馈使用问题或工具缺陷。Issue 是公开的，请勿附上 API Key、Apple 凭证、私人照片或完整收藏备份。

代码与文档采用 [MIT 许可证](LICENSE)。App 角色插画、品牌素材及同人卡包不适用 MIT，详见 [素材说明](ASSET-NOTICE.md)。
