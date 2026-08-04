from __future__ import annotations

import re
from typing import Tuple

from src.config import ModelConfig


def estimate_tokens(text: str) -> int:
    # 简单可复现估算：英文约 4 字符/token，中文按 1.5 字符/token 粗估。
    if not text:
        return 0
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    other = max(len(text) - cjk, 0)
    return max(1, int(cjk / 1.5 + other / 4))


class OpenAICompatibleClient:
    def __init__(self, config: ModelConfig):
        self.config = config
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("缺少 openai 依赖，请先 pip install -r requirements.txt") from exc
        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url)

    def chat(self, system_prompt: str, user_prompt: str) -> Tuple[str, int, int]:
        response = self.client.chat.completions.create(
            model=self.config.name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None) or estimate_tokens(system_prompt + "\n" + user_prompt)
        output_tokens = getattr(usage, "completion_tokens", None) or estimate_tokens(content)
        return content.strip(), input_tokens, output_tokens


class MockLLMClient:
    """离线演示客户端。

    它不追求真实翻译质量，只保证系统在无 API Key 时能跑通完整链路。
    答辩时如果有真实模型，应将 MOCK_MODE=false。
    """

    DICTIONARY = {
        "artificial intelligence": "人工智能",
        "large language models": "大语言模型",
        "large language model": "大语言模型",
        "machine learning": "机器学习",
        "reinforcement learning": "强化学习",
        "neural network": "神经网络",
        "transformer": "Transformer",
        "clinical diagnosis": "临床诊断",
        "data privacy": "数据隐私",
        "supply chain": "供应链",
        "risk management": "风险管理",
        "carbon neutrality": "碳中和",
        "contract": "合同",
        "liability": "责任",
        "inflation": "通货膨胀",
        "diabetes": "糖尿病",
        "mitochondria": "线粒体",
        "immune response": "免疫反应",
        "cloud computing": "云计算",
        "online learning platforms": "在线学习平台",
        "portfolio diversification": "投资组合分散化",
        "expected returns": "预期收益",
        "market volatility": "市场波动",
        "central bank": "中央银行",
        "policy decisions": "政策决策",
        "blood glucose levels": "血糖水平",
        "dietary recommendations": "饮食建议",
        "force majeure": "不可抗力",
        "consumer behavior": "消费者行为",
        "coordinated action": "协同行动",
        "transforming": "正在改变",
        "remains": "仍然是",
        "hospitals": "医院",
        "delayed": "延迟的",
        "shipments": "发货",
        "energy": "能源",
        "transportation": "交通",
        "manufacturing": "制造业",
        "states": "规定",
        "limited": "受限",
        "delay": "延迟",
        "caused": "导致",
        "high": "高",
        "reduce": "降低",
        "household": "家庭",
        "purchasing power": "购买力",
        "influence": "影响",
        "should": "应该",
        "monitor": "监测",
        "follow": "遵循",
        "personalized": "个性化的",
        "generate": "生成",
        "cells": "细胞",
        "while": "同时",
        "protects": "保护",
        "body": "身体",
        "pathogens": "病原体",
        "based": "基于",
        "architectures": "架构",
        "fluent": "流畅的",
        "text": "文本",
        "may": "可能",
        "produce": "产生",
        "hallucinations": "幻觉",
        "helps": "帮助",
        "investors": "投资者",
        "balance": "平衡",
        "potential": "潜在的",
        "provide": "提供",
        "timely": "及时的",
        "adjust": "调整",
        "study strategies": "学习策略",
        "is": "是",
        "are": "是",
        "can": "能够",
        "but": "但是",
        "and": "和",
        "requires": "需要",
        "improved": "改进了",
        "strategy": "策略",
        "concern": "关注点",
        "major": "主要的",
        "company": "公司",
        "patients": "患者",
        "students": "学生",
        "platforms": "平台",
        "feedback": "反馈",
    }

    def __init__(self, config: ModelConfig):
        self.config = config
        # 预编译词表 regex，大幅提升模拟翻译速度
        self._dict_sorted = sorted(self.DICTIONARY.items(), key=lambda x: len(x[0]), reverse=True)
        self._patterns = [(re.compile(rf"\b{re.escape(k)}\b" if k.replace(" ", "").isalpha() else re.escape(k), re.IGNORECASE), v)
                          for k, v in self._dict_sorted]
        # 单次编译清理正则
        self._clean_re = re.compile(r"\b(the|a|an|to|for|of|in|on)\b", re.IGNORECASE)

    def chat(self, system_prompt: str, user_prompt: str) -> Tuple[str, int, int]:
        text_match = re.search(r"待翻译文本：\s*(.*?)\s*(?:\n\n|$)", user_prompt, flags=re.S)
        text = text_match.group(1).strip() if text_match else user_prompt.strip()
        translated = self._pseudo_translate_fast(text)
        if self.config.key == "model_b":
            translated = translated.replace("但是", "但").replace("主要的关注点", "核心关切")
            prefix = "【模型B模拟译文】"
        else:
            prefix = "【模型A模拟译文】"
        output = prefix + translated
        return output, estimate_tokens(system_prompt + user_prompt), estimate_tokens(output)

    def _pseudo_translate_fast(self, text: str) -> str:
        result = text
        for pattern, target in self._patterns:
            result = pattern.sub(target, result)
        result = result.replace(",", "，").replace(".", "。").replace(";", "；")
        result = self._clean_re.sub("", result)
        result = re.sub(r"\s+", " ", result).strip()
        return result


def build_client(config: ModelConfig, mock_mode: bool):
    if mock_mode or not config.enabled:
        return MockLLMClient(config)
    return OpenAICompatibleClient(config)
