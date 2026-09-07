# 贡献指南

感谢你有兴趣改进 `novel-continuation`！本仓库只包含**工具与方法层**，不附带任何受版权保护的小说素材。请阅读本指南后再提交改动。

## 目录约定

| 目录 | 内容 |
|---|---|
| `scripts/` | 确定性处理脚本（切分/探知/校验/导出/风格评分），**可量化的逻辑必须落在这里** |
| `style_metrics.py` | 公共文体指标模块，供多个脚本共用；新增指标优先加在这里 |
| `references/` | 方法论文档（工作流/分析维度/文风/范式库/合规） |
| `schemas/` | JSON Schema 契约，与 `templates/` 对应 |
| `prompts/` | 提示词模板（标准流程 + 轻量模式） |
| `tests/` | 脚本层测试 + 合规 fixture |

## 开发流程

1. **改代码前写测试**：脚本逻辑的改动请先补 `tests/test_*.py` 用例。
2. **保持向后兼容**：不改动已有 CLI 参数与函数签名；新增能力以附加字段/新参数形式加入。
3. **只添加描述性内容，不复制原文**：任何 `references/` 或 `README` 中的示例都必须为**自创、无版权**文本（新内容请放 `references/style_samples.md` 或 `tests/fixtures/`，不要以真实受版权作品为样例）。
4. **合规红线**：不加入任何受版权小说的原文、续写或评价断言；不宣称续写代表原作者；文风描述只针对抽象叙事特征。

## 测试与校验

```bash
python -m pytest -q          # 全量测试
python scripts/validate_json.py --path <json>   # 校验 JSON 符合 schema
```

## 提交规范

- 提交信息用简洁的祈使句（如 `Add layered style similarity scoring`）。
- 一次提交聚焦一个改动点；不提交 `projects/`、`__pycache__/`、`.pytest_cache/` 等运行时产物（已在 `.gitignore` 中排除）。
- 提 PR 前请确认 `python -m pytest -q` 全绿。
