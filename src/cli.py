from __future__ import annotations

import argparse
import json

from src.pipeline import TranslationPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="多模型协作翻译与审校系统 CLI")
    parser.add_argument("--text", required=True, help="待翻译文本")
    parser.add_argument("--source-lang", default=None, help="源语言，例如 English")
    parser.add_argument("--target-lang", default=None, help="目标语言，例如 Chinese")
    args = parser.parse_args()

    pipeline = TranslationPipeline()
    result = pipeline.run(args.text, source_lang=args.source_lang, target_lang=args.target_lang)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
