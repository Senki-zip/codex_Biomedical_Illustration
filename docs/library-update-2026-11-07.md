# 素材库扩充记录 · 2026-11-07

插件版本：1.1.0。

- BioIcons：按上游最新 main 与 2,846 个文件的 Git blob 哈希核对，仍为原固定提交；下载变化文件数为 0，没有虚报新增。
- Reactome：完整目录 2,571 条，已下载 2,571 个 SVG，失败 0 条。保留图标 ID、设计者、设计者网址、描述、来源及 CC BY 4.0 许可，并导出 CSHL、OICR 和 EMBL-EBI 署名。
- 合计 5,400 条索引，5,396 个可解析 SVG；内容去重后 5,393 个可用图标。保留原有 4 个损坏文件和 1 个缺少作者目录的未索引原件。
- 5,400 条索引的文件 SHA-256 验证通过；未新增上游损坏文件。
- 5 项行为测试通过：多来源更新保留、去重与来源筛选、混合许可文本保留、标准 SVG 实体解析、无效源文件拒绝，以及旧版归档导入保留 Reactome。
- 已从新来源选取真实图标生成 SVG、PNG 和带署名的预览，并目视检查。

完整机器可读记录见 [library-update-2026-11-07.json](library-update-2026-11-07.json)。上游许可声明见 [Reactome Icon Library](https://reactome.org/icon-lib)。NIH BioArt 未在本版中下载。

![新增素材预览](reactome-preview.png)
