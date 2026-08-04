# DEPLOY：部署说明与常见问题

## 1. 环境要求

- Python 3.10 或以上。
- 推荐使用虚拟环境。
- 如需 OCR，需要本机安装 Tesseract OCR。

## 2. 安装步骤

```bash
cd translation_review_system
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 3. 配置环境变量

复制样例：

```bash
cp .env.example .env
```

无 API Key 时：

```env
MOCK_MODE=true
```

有真实模型接口时：

```env
MOCK_MODE=false
MODEL_A_BASE_URL=https://api.openai.com/v1
MODEL_A_API_KEY=xxx
MODEL_A_NAME=gpt-4o-mini

MODEL_B_BASE_URL=https://api.openai.com/v1
MODEL_B_API_KEY=xxx
MODEL_B_NAME=gpt-4.1-mini
```

如果使用 LM Studio 或 Ollama 的 OpenAI 兼容接口，把 `BASE_URL` 改成本地地址即可。

## 4. 启动方式

### Streamlit 界面

```bash
streamlit run src/app.py
```

浏览器打开 Streamlit 提示的本地地址。

### CLI 命令行

```bash
python -m src.cli --text "Artificial intelligence improves clinical diagnosis."
```

## 5. OCR 配置

### Windows

1. 安装 Tesseract。
2. 在 `.env` 中配置：

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### macOS

```bash
brew install tesseract
```

### Linux

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim
```

## 6. 常见问题

### Q1：启动后译文前面显示“模型A模拟译文”

说明当前是 `MOCK_MODE=true`。这是离线演示模式。要接真实模型，需要填 API Key 并改为：

```env
MOCK_MODE=false
```

### Q2：OpenAI API 调用失败

检查：

1. API Key 是否正确。
2. BASE_URL 是否是 OpenAI 兼容地址。
3. 模型名称是否存在。
4. 网络是否可访问。

### Q3：OCR 失败

OCR 是进阶功能，不影响主流程。检查：

1. 是否安装 Tesseract。
2. `TESSERACT_CMD` 路径是否正确。
3. 图片是否清晰。

### Q4：导入 `src` 模块失败

确保在项目根目录执行命令：

```bash
cd translation_review_system
streamlit run src/app.py
```

### Q5：评分看起来不够智能

这是设计选择。课题要求算法和规则可复现，所以评分主要由规则引擎完成。LLM 只负责翻译和语言建议。

## 7. 打包提交

提交前删除：

```text
.env
.venv/
__pycache__/
.pytest_cache/
```

打包：

```bash
zip -r 21_组名.zip translation_review_system -x "*.env" "*/.venv/*" "*/__pycache__/*"
```
