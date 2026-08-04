# 多模型协作翻译与审校系统

这是序号 21「多模型协作翻译与审校系统」的可运行项目骨架。

## 一、项目目标

系统接收待翻译文本或 Markdown 文档，先做文本复杂度评估，再调用两个翻译模型生成译文，随后用可复现的规则评分模型进行审校打分，输出：

- 原文
- 文本复杂度与路由决策
- 两个模型的译文
- 扣分明细与总分
- 推荐译文
- 信达雅评价与修改建议
- 模型耗时与成本统计

## 二、核心功能对应课题要求

| 课题要求 | 本项目实现位置 |
|---|---|
| 句子长度、嵌套从句数、术语密度复杂度评估 | `src/complexity.py` |
| 按复杂度做路由决策 | `src/router.py` |
| 至少 5 条量化扣分规则 | `src/scoring.py` |
| 两个模型翻译同一文本并对比 | `src/translator.py`、`src/app.py` |
| 记录评分与耗时 | `src/metrics.py` |
| 输出原文、多译文、评分表、推荐译文 | `src/app.py` |
| 审校子 Agent：信达雅评分与建议 | `src/reviewer_agent.py` |
| 图片 OCR 后翻译 | `src/ocr.py` |
| 批量 Markdown 文档翻译且保持目录结构 | `src/batch_doc.py` |
| 中间件统计模型成本与耗时 | `src/metrics.py` |

## 三、快速启动

### 1. 创建环境

```bash
cd translation_review_system
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

复制配置样例：

```bash
cp .env.example .env
```

如果你有 OpenAI 兼容接口，填写：

```env
MODEL_A_BASE_URL=https://api.openai.com/v1
MODEL_A_API_KEY=你的key
MODEL_A_NAME=gpt-4o-mini
MODEL_A_PRICE_INPUT_PER_1K=0.00015
MODEL_A_PRICE_OUTPUT_PER_1K=0.0006

MODEL_B_BASE_URL=https://api.openai.com/v1
MODEL_B_API_KEY=你的key
MODEL_B_NAME=gpt-4.1-mini
MODEL_B_PRICE_INPUT_PER_1K=0.0004
MODEL_B_PRICE_OUTPUT_PER_1K=0.0016
```

没有 API Key 时可以使用离线演示模式：

```env
MOCK_MODE=true
```

### 3. 启动界面

```bash
streamlit run src/app.py
```

### 4. 命令行测试

```bash
python -m src.cli --text "Artificial intelligence is transforming clinical diagnosis, but data privacy remains a major concern."
```

## 四、推荐答辩演示流程

1. 输入一段普通文本，展示复杂度低、两个模型译文、评分与推荐译文。
2. 输入一段医学或法律文本，展示术语密度升高、路由策略变化。
3. 展示评分表，解释至少 5 条扣分规则如何计算。
4. 上传一张包含英文文字的图片，展示 OCR 后进入翻译流程。
5. 上传 Markdown 文档，展示标题层级不变、正文被翻译。
6. 打开耗时/成本统计，说明中间件记录了每个模型的调用耗时与估算成本。

## 五、项目结构

```text
translation_review_system/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   ├── benchmark_texts.jsonl
│   └── term_glossary.csv
├── docs/
│   ├── REQUIREMENTS.md
│   ├── DESIGN.md
│   ├── ANALYSIS.md
│   ├── DEPLOY.md
│   ├── SUMMARY.md
│   ├── CLEANING.md
│   └── TEST_CASES.md
├── src/
│   ├── app.py
│   ├── batch_doc.py
│   ├── cli.py
│   ├── complexity.py
│   ├── config.py
│   ├── llm_client.py
│   ├── metrics.py
│   ├── ocr.py
│   ├── reviewer_agent.py
│   ├── router.py
│   ├── scoring.py
│   ├── tools.py
│   └── translator.py
└── tests/
    ├── test_complexity.py
    └── test_scoring.py
```

## 六、注意事项

- 真正提交时不要提交 `.env`、`.venv`、`__pycache__`。
- 若使用真实模型，答辩前提前测试网络与 Key。
- 如果 OCR 不可用，说明是可选进阶功能，核心链路仍可通过文本输入演示。
