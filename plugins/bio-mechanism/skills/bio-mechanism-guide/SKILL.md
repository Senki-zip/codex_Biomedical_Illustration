---
name: bio-mechanism-guide
description: Explain how to use the Biomedical Illustration plugin and its skills, check the installed local artwork library, and guide users through finding SVG assets, exporting a BioRender import bundle, or composing a first mechanism diagram. Use for onboarding, usage instructions, and requests such as how to use this plugin or 使用教程.
---

# 科研机制图插件使用指南

使用中文或用户当前使用的语言介绍插件，并根据用户目标给出可直接执行的下一步。用户已给出绘图任务时，直接进入相应流程，不要求用户先完成教程。

## 定位本机插件

本文件所在目录为 `<guide-dir>`。实际绘图技能位于同级目录 `../bio-mechanism/`，记为 `<draw-dir>`。从本文件的位置解析路径，不依赖当前工作目录，也不要硬编码用户名或 Codex 缓存版本。

先阅读 [绘图技能](../bio-mechanism/SKILL.md)，并运行：

```bash
python3 <draw-dir>/scripts/bioassets.py stats
```

根据实际输出说明素材数量与下载状态。不要把检索条目数、原始文件数和可用 SVG 数混为一谈。普通入门只运行 `stats`；用户要求完整性审计或出现素材损坏时再使用 `stats --verify`。

## 说明两种 skill 的用途

- `$bio-mechanism-guide`：介绍操作方法、检查素材库、协助完成第一次使用。
- `$bio-mechanism`：执行素材检索、预览、导出，以及可编辑 SVG 机制图组装。

也可以直接用自然语言提出任务，插件技能允许自动选择。例如：

> 使用科研机制图素材库，找细胞核、DNA、蛋白和细胞膜受体的素材，生成候选图册。

> 使用 $bio-mechanism，找 6 个 CC0 科研图标，导出 SVG 和来源记录，供我上传到 BioRender。

> 使用 $bio-mechanism，根据以下机制关系绘图：A 激活 B，B 抑制 C，B 到 D 为待验证关系。请提供 SVG、PNG 预览和素材署名。

## 按目标带用户操作

**找素材。** 将用户的对象转为中英文关键词；调用 `bioassets.py search`，用 `--gallery` 生成候选图册。保留返回的真实素材 ID。按需要使用 `--author` 保持风格一致，或 `--license cc-0` 限定许可。

**导入 BioRender。** 选择真实 ID 后调用 `bioassets.py export`；提供 SVG、`ATTRIBUTION.md`、`assets.json` 和许可文件。告知用户通过 BioRender 的 Uploads 上传。插件不包含 BioRender 账号连接、专有图标或订阅权益；上传 SVG 不保证内部路径能逐个编辑。

**画机制图。** 根据用户提供的分子关系和布局要求建立 JSON 场景，按 [场景格式](../bio-mechanism/references/scene-format.md) 调用 `compose`。需要演示时可使用 `<draw-dir>/assets/examples/generic-mechanism.scene.json`，并清楚标为通用示例。通过 `render.cjs` 生成预览并检查，交付 SVG、场景 JSON 和素材署名。可选渲染器不可用时保留已生成的 SVG，并说明 PNG 尚未生成。

如果用户只问“怎么用”，简洁介绍以上流程和示例提示语即可，不自动生成不相关图。若用户要求开始绘图但尚未提供机制关系，询问核心分子、激活／抑制关系及使用场景；同时可检索已经明确的素材。

## 常见问题

- **扩充或更新素材库：** 按绘图技能的“Update downloaded sources”说明运行 `sync_library.py bioicons` 或 `sync_library.py reactome`，再检查统计和完整性。用 `--source BioIcons` 或 `--source Reactome` 筛选。可用数量按内容哈希去重，重复条目的 ID 和来源仍保留。

- **安装后找不到 skill：** 新开对话；仍未出现时重启 Codex。可以使用 `codex plugin list` 检查已安装和启用状态，不主动删除或重装其他插件。
- **查不到对象：** 尝试英文术语、同义词和更宽的分类；说明通用图标不能证明某一特定分子的身份。
- **需要修改：** 通过场景 JSON 调整对象、标签和连线，重新生成 SVG；单个素材改色后保留原始来源并记录修改。
- **论文署名：** 使用导出包中的逐素材记录。各图标许可不同，不能把整个库统一称为公共领域或 MIT。

详细来源见 [sources.md](../bio-mechanism/references/sources.md)。安装方法与仓库结构见插件所在仓库的 README；技能本身必须能在安装缓存中独立工作，不依赖仓库 README 的存在。
