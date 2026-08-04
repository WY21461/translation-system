# TEST_CASES：测试用例与预期结果

## 1. 核心流程测试

| 编号 | 输入 | 预期结果 | 实际验证方式 |
|---|---|---|---|
| TC01 | `Artificial intelligence improves clinical diagnosis.` | 命中 artificial intelligence、clinical diagnosis，输出两个译文和推荐译文 | Streamlit 文本翻译页 |
| TC02 | `Revenue increased by 25% in 2024.` | 如果译文遗漏 25% 或 2024，评分器扣“数字/单位遗漏” | `tests/test_scoring.py` |
| TC03 | 包含 `data privacy` 的文本 | 如果译文未出现“数据隐私”，扣“专业术语不一致” | Streamlit 文本翻译页 |
| TC04 | Markdown 文档含 `# Title`、列表、代码块 | 翻译后保留标题层级、列表前缀、代码块 | Streamlit Markdown 页 |
| TC05 | 空文本 | 系统提示“输入文本不能为空”，不直接 traceback | Streamlit 文本翻译页 |

## 2. 10 段 benchmark 测试

数据文件：`data/benchmark_texts.jsonl`。

| ID | 领域 | 测试目的 |
|---:|---|---|
| 1 | technology/medicine | 检查 artificial intelligence、clinical diagnosis、data privacy 术语 |
| 2 | business | 检查 supply chain、risk management 术语 |
| 3 | environment | 检查 carbon neutrality 术语 |
| 4 | law | 检查 contract、liability 术语 |
| 5 | economics | 检查 inflation 术语 |
| 6 | medicine | 检查 diabetes 术语 |
| 7 | biology | 检查 mitochondria、immune response 术语 |
| 8 | technology | 检查 large language model、transformer 术语 |
| 9 | finance | 检查普通金融文本翻译表现 |
| 10 | education | 检查教育文本翻译表现 |

## 3. 单元测试

运行：

```bash
pytest -q
```

已有测试：

- `tests/test_complexity.py`
  - 测试术语命中。
  - 测试长句复杂度高于短句。
- `tests/test_scoring.py`
  - 测试数字遗漏扣分。
  - 测试术语不一致扣分。
  - 测试较好译文得分较高。

## 4. 答辩现场推荐测试输入

### 普通文本

```text
Online learning platforms should provide timely feedback so students can adjust their study strategies.
```

### 专业文本

```text
Artificial intelligence is transforming clinical diagnosis, but data privacy remains a major concern for hospitals.
```

### 法律文本

```text
The contract states that liability shall be limited if the delay is caused by force majeure.
```

### Markdown 文档

```markdown
# Project Overview

Artificial intelligence can improve productivity.

## Risk

- Data privacy is important.
- The contract defines liability.
```

## 5. 测试结果记录表模板

| 测试编号 | 输入摘要 | 预期结果 | 实际结果 | 是否通过 | 备注 |
|---|---|---|---|---|---|
| TC01 | AI 医学句子 | 双模型输出，术语命中 | 待填写 | 待填写 | 现场运行后截图 |
| TC02 | 数字年份句子 | 数字遗漏会扣分 | 待填写 | 待填写 | 可用单元测试证明 |
| TC03 | Markdown | 结构保持 | 待填写 | 待填写 | 截图 |
| TC04 | OCR 图片 | 提取文字并翻译 | 待填写 | 待填写 | OCR 依赖本机环境 |
| TC05 | 空输入 | 友好提示 | 待填写 | 待填写 | 边界测试 |
