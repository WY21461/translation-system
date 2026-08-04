"""
多模型协作翻译与审校系统
全中文简约界面 · 左右分栏 · 并行翻译 · 规率评分
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.batch_doc import translate_markdown
from src.config import load_config
from src.ocr import extract_text_from_image
from src.pipeline import TranslationPipeline

st.set_page_config(
    page_title="多模型协作翻译与审校系统",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 设计系统 CSS
# ============================================================
CSS = """
<style>
:root {
  --panel:      #F7F8FC;
  --surface:    #FFFFFF;
  --border:     #E5E7EB;
  --text:       #1E1F2B;
  --secondary:  #6B7280;
  --muted:      #9CA3AF;
  --primary:    #2B6FF2;
  --primary-hv: #1A5AD9;
  --primary-bg: #EDF2FD;
  --success:    #16A34A;
  --success-bg: #EDF8F1;
  --error:      #DC2626;
  --error-bg:   #FEF2F2;
  --radius:     6px;
  --radius-lg:  10px;
}

/* 全局 */
.stApp { background: var(--panel); }
.block-container { padding: 0.6rem 1.5rem 1.5rem; max-width: 1400px; }
#MainMenu, footer, header { display: none !important; }

/* 标题 */
h1,h2,h3,h4 { font-weight: 600; color: var(--text); letter-spacing: -0.01em; }
h1 { font-size: 1.3rem; }
h2 { font-size: 1.1rem; }
h3 { font-size: 1rem; }
h4 { font-size: 0.9rem; }

/* 正文/次要文字 */
p, span, div { color: var(--text); }

/* ── 顶部标题栏 ── */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding: 0.25rem 0;
  margin-bottom: 0;
}
.topbar .title-group {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
  flex-wrap: wrap;
  min-width: 0;
}
.topbar .brand {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  line-height: 1.3;
}
.topbar .subtitle {
  font-size: 0.72rem;
  color: var(--secondary);
  white-space: nowrap;
}
.topbar .mock-tag {
  font-size: 0.68rem;
  background: #FEF9EE;
  color: #D97706;
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

/* ── 导航标签 ── */
.nav-row {
  display: flex;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}
.nav-btn {
  padding: 0.45rem 1rem;
  font-size: 0.84rem;
  font-weight: 500;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--secondary);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.nav-btn:hover { border-color: var(--primary); color: var(--primary); }
.nav-btn.active { background: var(--primary); border-color: var(--primary); color: #fff; }

/* ── 按钮 ── */
.stButton > button {
  font-weight: 500; font-size: 0.84rem; border-radius: var(--radius);
  border: 1px solid var(--border); background: var(--surface); color: var(--text);
  padding: 0.45rem 1rem; transition: all 0.12s;
}
.stButton > button:hover {
  border-color: var(--primary); color: var(--primary);
  transform: translateY(-1px); box-shadow: 0 2px 8px rgba(43,111,242,0.12);
}
.stButton > button:active { transform: translateY(0); }
.stButton > button[kind="primary"] {
  background: var(--primary); border-color: var(--primary); color: #fff;
}
.stButton > button[kind="primary"]:hover {
  background: var(--primary-hv); border-color: var(--primary-hv); color: #fff;
  transform: translateY(-1px); box-shadow: 0 2px 12px rgba(43,111,242,0.25);
}
.stButton > button[kind="primary"]:active { transform: translateY(0); }

/* ── 输入框 ── */
textarea, input {
  border-radius: var(--radius) !important;
  border: 1px solid var(--border) !important;
  font-size: 0.86rem !important;
}
textarea:focus, input:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 2px var(--primary-bg) !important;
}

/* ── 表格 ── */
[data-testid="stDataFrame"] {
  border-radius: var(--radius); overflow: hidden;
  border: 1px solid var(--border);
}
[data-testid="stDataFrame"] th {
  background: #F9FAFB; font-weight: 600; color: var(--secondary);
  font-size: 0.72rem; padding: 0.5rem 0.7rem;
  border-bottom: 1px solid var(--border);
}
[data-testid="stDataFrame"] td {
  font-size: 0.82rem; padding: 0.4rem 0.7rem;
  border-bottom: 1px solid #F3F4F6; color: var(--text);
}

/* ── 分隔线 ── */
hr { border: none; border-top: 1px solid var(--border); margin: 0.6rem 0; }

/* ── Radio 水平导航 ── */
[data-testid="stRadio"] > div { gap: 0.4rem; }
[data-testid="stRadio"] label {
  padding: 0.4rem 0.9rem; border: 1px solid var(--border);
  border-radius: var(--radius); font-size: 0.84rem; font-weight: 500;
  color: var(--secondary); background: var(--surface);
  transition: all 0.12s; cursor: pointer;
}
[data-testid="stRadio"] label:hover { border-color: var(--primary); color: var(--primary); }
[data-testid="stRadio"] input:checked + label, [data-testid="stRadio"] [data-selected="true"] label {
  background: var(--primary) !important; border-color: var(--primary) !important; color: #fff !important;
}

/* ── 展开面板 ── */
[data-testid="stExpander"] {
  background: var(--surface); border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important; margin-bottom: 0.4rem;
}
[data-testid="stExpander"] summary { font-weight: 500; font-size: 0.84rem; }

/* ── 指标卡片 ── */
.metric-row { display: flex; gap: 0.6rem; flex-wrap: wrap; margin: 0.4rem 0; }
.metric-card {
  flex: 1; min-width: 90px; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--radius);
  padding: 0.6rem 0.8rem;
}
.metric-card .m-label { font-size: 0.65rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.15rem; }
.metric-card .m-value { font-size: 1.2rem; font-weight: 700; color: var(--text); }
.metric-card .m-sub { font-size: 0.66rem; color: var(--secondary); margin-top: 0.05rem; }

/* ── 译文对比双栏 ── */
.cmp-grid { display: flex; gap: 0.8rem; margin: 0.5rem 0; }
.cmp-col {
  flex: 1; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 1rem 1.1rem 0.6rem; min-width: 0;
}
.cmp-col .model-tag {
  display: inline-block; font-size: 0.68rem; font-weight: 700;
  color: var(--primary); background: var(--primary-bg);
  padding: 0.1rem 0.55rem; border-radius: 999px; margin-bottom: 0.5rem;
}
.cmp-col .trans-body { font-size: 0.86rem; line-height: 1.75; color: var(--text); margin: 0.4rem 0 0.6rem; }
.cmp-col .score-line {
  display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;
  padding-top: 0.5rem; border-top: 1px solid var(--border);
}

/* ── 分数药丸 ── */
.pill {
  display: inline-block; padding: 0.15rem 0.55rem; border-radius: 999px;
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.02em;
}
.pill-g { background: var(--success-bg); color: var(--success); }
.pill-r { background: var(--error-bg);   color: var(--error);   }

/* ── 分数色彩阈值  绿≥80 / 红<60 ── */
.pill-s0 { background: var(--success-bg); color: var(--success); }
.pill-s1 { background: #FEF9EE; color: #D97706; }
.pill-s2 { background: var(--error-bg); color: var(--error); }

/* ── 推荐译文 ── */
.rec {
  background: var(--success-bg); border: 1px solid #C8E6D0;
  border-left: 4px solid var(--success); border-radius: var(--radius-lg);
  padding: 0.9rem 1.1rem; margin: 0.5rem 0;
}
.rec .rec-hd { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--success); margin-bottom: 0.2rem; }
.rec .rec-txt { font-size: 0.9rem; line-height: 1.8; color: var(--text); }

/* ── 路由提示 ── */
.route-bar {
  background: var(--primary-bg); border-left: 3px solid var(--primary);
  border-radius: var(--radius); padding: 0.5rem 0.9rem; margin: 0.4rem 0; font-size: 0.82rem;
}

/* ── 空状态 ── */
.empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 340px; text-align: center; color: var(--muted);
}
.empty .e-title { font-size: 0.92rem; font-weight: 600; color: var(--secondary); margin-top: 0.5rem; }
.empty .e-desc { font-size: 0.78rem; max-width: 300px; margin-top: 0.25rem; }

/* 响应式 */
@media (max-width: 1000px) { .cmp-grid { flex-direction: column; } .block-container { padding: 0.8rem; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------------------------------------
# 缓存
# ------------------------------------------------------------
@st.cache_resource
def get_pipeline() -> TranslationPipeline:
    return TranslationPipeline(load_config())

pipeline = get_pipeline()
config = load_config()

# ------------------------------------------------------------
# 会话
# ------------------------------------------------------------
for k, v in [("last_result", None), ("md_result", None), ("nav", "文本翻译")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ------------------------------------------------------------
# 分数色彩
# ------------------------------------------------------------
def _sc(score: int) -> str:
    """0=绿(≥80) 1=黄(≥60) 2=红(<60)"""
    return "s0" if score >= 80 else ("s1" if score >= 60 else "s2")

def _pill(score: int) -> str:
    return f'<span class="pill pill-{_sc(score)}">{score}</span>'

def metric_html(tiles: list) -> str:
    p = ['<div class="metric-row">']
    for t in tiles:
        s = f'<div class="m-sub">{t["sub"]}</div>' if t.get("sub") else ""
        p.append(f'<div class="metric-card"><div class="m-label">{t["label"]}</div><div class="m-value">{t["value"]}</div>{s}</div>')
    p.append('</div>')
    return "".join(p)

def _cmp_col(label: str, trans: str, score: int,
             fidelity: int, express: int, elegance: int,
             ded: list, sugg: list, comment: str) -> str:
    pills = f'{_pill(fidelity)} {_pill(express)} {_pill(elegance)}'
    ded_html = ""
    if ded:
        items = "".join(
            f'<tr><td style="padding:0.2rem 0.4rem;font-size:0.73rem;border-bottom:1px solid #F3F4F6;">{d.get("rule","")}</td>'
            f'<td style="padding:0.2rem 0.4rem;font-size:0.73rem;text-align:right;border-bottom:1px solid #F3F4F6;color:var(--error);">-{d.get("points","")}</td></tr>'
            for d in ded
        )
        ded_html = (
            '<details style="margin-top:0.5rem;font-size:0.73rem;">'
            '<summary style="cursor:pointer;color:var(--secondary);">扣分明细</summary>'
            f'<table style="width:100%;margin-top:0.2rem;">{items}</table></details>'
        )
    sugg_html = "".join(
        f'<div style="font-size:0.71rem;color:var(--secondary);padding:0.08rem 0;">· {s}</div>'
        for s in sugg
    )
    return f"""<div class="cmp-col">
<div class="model-tag">{label}</div>
<div class="trans-body">{trans}</div>
<div class="score-line">
<span style="font-size:0.68rem;font-weight:600;color:var(--muted);text-transform:uppercase;">总分</span>{_pill(score)}
<span style="font-size:0.66rem;color:var(--muted);margin:0 0.2rem;">信·达·雅</span>{pills}
</div>{ded_html}
<div style="margin-top:0.4rem;font-size:0.73rem;color:var(--secondary);font-style:italic;">{comment}</div>{sugg_html}
</div>"""

def render_result(result: dict):
    cpx = result["complexity"]
    route = result["route"]

    st.markdown("### 复杂度评估与路由")
    st.markdown(metric_html([
        {"label": "复杂度总分", "value": str(cpx["total_score"]), "sub": None},
        {"label": "复杂度等级", "value": cpx["level"], "sub": None},
        {"label": "平均句长", "value": f'{cpx["avg_sentence_length"]:.1f}', "sub": "词/句"},
        {"label": "嵌套从句", "value": str(cpx["nested_clause_count"]), "sub": "个"},
    ]), unsafe_allow_html=True)

    terms = cpx.get("matched_terms", [])
    if terms:
        st.markdown(
            f'<span style="font-size:0.78rem;color:var(--secondary);">命中术语：{" · ".join(terms)}</span>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="route-bar"><strong>{route["strategy"]}</strong> '
        f'<span style="color:var(--secondary);">— {route["reason"]}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    # 翻译对比
    st.markdown("### 译文对比")
    cols = []
    for item in result["translations"]:
        c = item["candidate"]
        s = item["score"]
        r = item["review"]
        cols.append(_cmp_col(c["model_name"], c["translation"], s["score"],
                             r["fidelity_score"], r["expressiveness_score"], r["elegance_score"],
                             s.get("deductions", []), r.get("suggestions", []),
                             r.get("overall_comment", "")))
    st.markdown(f'<div class="cmp-grid">{"".join(cols)}</div>', unsafe_allow_html=True)

    # 汇总表
    rows = []
    for item in result["translations"]:
        c = item["candidate"]
        s = item["score"]
        r = item["review"]
        rows.append({
            "模型": c["model_name"], "规则分": s["score"],
            "信": r["fidelity_score"], "达": r["expressiveness_score"],
            "雅": r["elegance_score"], "耗时": f'{c["latency_seconds"]:.2f}s',
            "成本": f'${c["estimated_cost"]:.5f}',
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # 推荐
    best = result["recommended"]
    bc = best["candidate"]
    bs = best["score"]
    st.markdown("### 推荐译文")
    st.markdown(
        f'<div class="rec"><div class="rec-hd">推荐 — {bc["model_name"]}（规则分 {bs["score"]}）</div>'
        f'<div class="rec-txt">{bc["translation"]}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 调用统计")
    st.json(result["metrics"])


def translate_segment(text: str) -> str:
    return pipeline.run(text)["recommended"]["candidate"]["translation"]

# ============================================================
# 顶部 — 系统标题 + MOCK 提示
# ============================================================
st.markdown(
    f'<div class="topbar">'
    f'<div class="title-group">'
    f'<span class="brand">多模型协作翻译与审校系统</span>'
    f'<span class="subtitle">复杂度评估 · 双模型对比 · 规则评分 · 审校建议</span>'
    f'</div>'
    f'{"<span class=\"mock-tag\">MOCK 模式</span>" if config.mock_mode else ""}'
    f'</div>',
    unsafe_allow_html=True,
)


# 分隔线
st.markdown("<hr style='margin:0.25rem 0 0.4rem;'>", unsafe_allow_html=True)

# ── 导航 ──
NAV = ["文本翻译", "Markdown 批量翻译", "图片 OCR 翻译", "10 段评测"]
nav = st.radio("导航", NAV, horizontal=True, label_visibility="collapsed", key="nav")

# ============================================================
# 1. 文本翻译
# ============================================================
if nav == NAV[0]:
    L, R = st.columns([1, 1.4])
    with L:
        st.markdown("#### 待翻译文本")
        text = st.text_area(
            "源文本", label_visibility="collapsed", height=160,
            value="Artificial intelligence is transforming clinical diagnosis, but data privacy remains a major concern for hospitals.",
            placeholder="请输入待翻译的英文或其他源语言文本……",
        )
        c1, c2 = st.columns(2)
        with c1: source_lang = st.text_input("源语言", value=config.source_lang, placeholder="源语言")
        with c2: target_lang = st.text_input("目标语言", value=config.target_lang, placeholder="目标语言")

        b1, b2 = st.columns([2, 1])
        with b1: do_it = st.button("开始翻译与审校", type="primary", use_container_width=True)
        with b2:
            if st.button("清空统计", use_container_width=True):
                pipeline.reset_metrics()
                st.toast("已清空调用统计", icon="")

    with R:
        if do_it:
            with st.spinner("正在翻译与审校……"):
                try:
                    st.session_state.last_result = pipeline.run(text, source_lang=source_lang, target_lang=target_lang)
                except Exception as exc:
                    st.error(f"处理失败：{exc}")
                    st.session_state.last_result = None
        if st.session_state.last_result:
            render_result(st.session_state.last_result)
        else:
            st.markdown(
                '<div class="empty"><div class="e-title">准备就绪</div>'
                '<div class="e-desc">输入待翻译文本后点击"开始翻译与审校"，结果将显示在此区域。</div></div>',
                unsafe_allow_html=True,
            )

# ============================================================
# 2. Markdown 批量翻译
# ============================================================
elif nav == NAV[1]:
    L, R = st.columns([1, 1.4])
    with L:
        st.markdown("#### Markdown 文档")
        md_text = st.text_area(
            "Markdown", label_visibility="collapsed", height=260,
            value="# 项目概览\n\n人工智能可以提升生产力。\n\n## 风险\n\n- 数据隐私至关重要。\n- 合同明确了责任划分。\n",
            placeholder="粘贴 Markdown 文档……",
        )
        do_md = st.button("翻译 Markdown", type="primary", use_container_width=True)
    with R:
        if do_md:
            with st.spinner("正在批量翻译……"):
                try:
                    st.session_state.md_result = translate_markdown(md_text, translate_segment)
                except Exception as exc:
                    st.error(f"翻译失败：{exc}")
                    st.session_state.md_result = None
        mr = st.session_state.get("md_result")
        if mr:
            st.markdown("**原始目录结构**")
            st.code("\n".join(mr.outline) or "（无标题）")
            st.metric("已翻译片段", mr.translated_units)
            st.text_area("翻译结果", value=mr.translated_markdown, height=240)
            sr = pipeline.scorer.score(md_text, mr.translated_markdown, preserve_markdown=True)
            st.metric("结构保持评分", f"{sr.score} / 100")
            if sr.deductions:
                st.dataframe(pd.DataFrame([d.to_dict() for d in sr.deductions]), use_container_width=True, hide_index=True)
        else:
            st.markdown(
                '<div class="empty"><div class="e-title">Markdown 批量翻译</div>'
                '<div class="e-desc">粘贴 Markdown 文档并点击翻译，系统将翻译正文并保持标题与目录结构不变。</div></div>',
                unsafe_allow_html=True,
            )

# ============================================================
# 3. 图片 OCR 翻译
# ============================================================
elif nav == NAV[2]:
    L, R = st.columns([1, 1.4])
    with L:
        st.markdown("#### 上传图片")
        up = st.file_uploader("图片", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
        do_ocr = False; ocr_text = ""
        if up:
            with st.spinner("正在 OCR 识别……"):
                ocr_res = extract_text_from_image(up, config.tesseract_cmd)
                if ocr_res.warning: st.warning(ocr_res.warning)
                ocr_text = ocr_res.text
                st.text_area("OCR 识别结果", value=ocr_text, height=140)
                if ocr_text: do_ocr = st.button("翻译 OCR 文本", type="primary", use_container_width=True)
    with R:
        if do_ocr and ocr_text:
            with st.spinner("正在翻译……"):
                try:
                    st.session_state.last_result = pipeline.run(ocr_text)
                except Exception as exc:
                    st.error(f"翻译失败：{exc}")
                    st.session_state.last_result = None
        if do_ocr and st.session_state.last_result:
            render_result(st.session_state.last_result)
        elif not do_ocr:
            st.markdown(
                '<div class="empty"><div class="e-title">图片 OCR 翻译</div>'
                '<div class="e-desc">上传包含文字的图片，系统先提取文字再进行翻译审校。</div></div>',
                unsafe_allow_html=True,
            )

# ============================================================
# 4. 10段评测
# ============================================================
elif nav == NAV[3]:
    L, R = st.columns([1, 1.4])
    data_path = PROJECT_ROOT / "data" / "benchmark_texts.jsonl"
    with L:
        st.markdown("#### 评测样本")
        samples_data = []
        if data_path.exists():
            for line in data_path.read_text(encoding="utf-8").splitlines():
                if not line.strip(): continue
                s = json.loads(line)
                t = s["text"]
                samples_data.append({"ID": s["id"], "领域": s["domain"], "文本预览": t[:50] + "…" if len(t) > 50 else t})
            st.dataframe(pd.DataFrame(samples_data), use_container_width=True, hide_index=True)
        do_bench = st.button("运行 10 段评测", type="primary", use_container_width=True)
    with R:
        if do_bench:
            rows = []
            bar = st.progress(0, text="正在评测……")
            samples = []
            if data_path.exists():
                for line in data_path.read_text(encoding="utf-8").splitlines():
                    if line.strip(): samples.append(json.loads(line))
            total = len(samples)
            for i, s in enumerate(samples):
                bar.progress((i + 1) / total, text=f"评测中：{s['id']}（{s['domain']}）")
                try:
                    r = pipeline.run(s["text"])
                    for it in r["translations"]:
                        rows.append({
                            "样本ID": s["id"], "领域": s["domain"],
                            "模型": it["candidate"]["model_name"], "评分": it["score"]["score"],
                            "耗时(s)": it["candidate"]["latency_seconds"], "成本($)": it["candidate"]["estimated_cost"],
                        })
                except Exception as exc:
                    st.warning(f"{s['id']} 失败：{exc}")
            bar.empty()
            if rows:
                st.success(f"评测完成，{total} 样本，{len(rows)} 条记录")
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                st.download_button("下载评测 CSV", pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"),
                                   "benchmark_result.csv", "text/csv", use_container_width=True)
            else:
                st.warning("没有成功的评测结果。")
        else:
            st.markdown(
                '<div class="empty"><div class="e-title">批量评测套件</div>'
                '<div class="e-desc">运行 10 段不同领域文本，对比两个模型的翻译质量差异。</div></div>',
                unsafe_allow_html=True,
            )
