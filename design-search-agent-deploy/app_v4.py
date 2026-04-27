import os
import base64
from io import BytesIO
from urllib.parse import quote

import streamlit as st
from PIL import Image
from playwright.sync_api import sync_playwright
from openai import OpenAI


st.set_page_config(
    page_title="Design Research Agent V4",
    page_icon="✦",
    layout="wide"
)

defaults = {
    "need_text": "",
    "search_keyword": "",
    "analysis_results": [],
    "need_judgement": [],
    "design_advice": [],
    "platform_rankings": [],
    "search_strategy": {},
    "last_upload_sig": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


st.markdown("""
<style>
.block-container {
    max-width: 1240px;
    padding-top: 24px;
    padding-bottom: 56px;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top left, rgba(37,99,235,0.14), transparent 24%),
        radial-gradient(circle at top right, rgba(139,92,246,0.10), transparent 20%),
        linear-gradient(180deg, #08101E 0%, #0B1325 100%);
}
[data-testid="stHeader"] {
    background: transparent;
}
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", sans-serif;
    color: #E5EDF8;
}
.hero-title {
    font-size: 42px;
    font-weight: 800;
    line-height: 1.08;
    color: #F8FAFC;
    margin-bottom: 10px;
}
.hero-sub {
    font-size: 16px;
    line-height: 1.85;
    color: #B7C3D8;
    max-width: 920px;
    margin-bottom: 14px;
}
.pill {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(17,24,39,0.70);
    color: #D9E2F2;
    font-size: 12px;
    border: 1px solid rgba(148,163,184,0.16);
    margin-right: 8px;
    margin-bottom: 8px;
}
.top-status {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(10,18,34,0.72);
    border: 1px solid rgba(96,165,250,0.16);
    border-radius: 14px;
    padding: 12px 16px;
    margin-top: 8px;
    margin-bottom: 28px;
}
.top-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: #22C55E;
    flex-shrink: 0;
}
.top-status-text {
    font-size: 13px;
    color: #D8E2F1;
}
.section-title {
    font-size: 28px;
    font-weight: 800;
    color: #F8FAFC;
    margin: 0 0 14px 0;
}
.section-sub {
    font-size: 13px;
    line-height: 1.8;
    color: #AAB7CD;
    margin-bottom: 12px;
}
.tip-list {
    background: rgba(8,14,28,0.34);
    border: 1px solid rgba(148,163,184,0.10);
    border-radius: 14px;
    padding: 14px 16px;
}
.tip-list ul {
    margin: 0;
    padding-left: 18px;
}
.tip-list li {
    margin-bottom: 8px;
    color: #C8D3E6;
    line-height: 1.8;
}
.tip-list li:last-child {
    margin-bottom: 0;
}
.advice-card {
    background: rgba(13,22,40,0.72);
    border: 1px solid rgba(148,163,184,0.10);
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 18px;
}
.advice-title {
    font-size: 17px;
    line-height: 1.8;
    color: #F8FAFC;
    font-weight: 700;
}
.advice-sub {
    font-size: 13px;
    line-height: 1.8;
    color: #AAB7CD;
    margin-top: 8px;
}
.platform-card {
    min-height: 188px;
    background: linear-gradient(180deg, rgba(18,29,52,0.92) 0%, rgba(10,16,30,0.96) 100%);
    border: 1px solid rgba(96,165,250,0.10);
    border-radius: 16px;
    padding: 16px;
}
.platform-rank {
    font-size: 12px;
    font-weight: 700;
    color: #60A5FA;
    margin-bottom: 8px;
}
.platform-name {
    font-size: 18px;
    font-weight: 800;
    color: #F8FAFC;
    margin-bottom: 8px;
}
.platform-reason {
    font-size: 13px;
    line-height: 1.8;
    color: #A9B7CF;
}
.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(148,163,184,0.12);
    border-radius: 14px;
    padding: 14px;
    min-height: 110px;
}
.metric-label {
    font-size: 12px;
    color: #9FB0C9;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 22px;
    font-weight: 800;
    color: #F8FAFC;
    margin-bottom: 6px;
}
.metric-sub {
    font-size: 12px;
    color: #AAB7CD;
}
.empty-card {
    background: rgba(13,22,40,0.60);
    border: 1px dashed rgba(148,163,184,0.18);
    border-radius: 16px;
    padding: 22px 20px;
}
.empty-title {
    font-size: 20px;
    font-weight: 700;
    color: #F8FAFC;
    margin-bottom: 8px;
}
.empty-sub {
    font-size: 14px;
    line-height: 1.8;
    color: #AAB7CD;
}
.result-card-title {
    font-size: 16px;
    line-height: 1.6;
    font-weight: 700;
    color: #F8FAFC;
    min-height: 64px;
    margin-top: 12px;
    margin-bottom: 6px;
}
.result-card-meta {
    font-size: 12px;
    color: #9FB0C9;
    margin-top: 8px;
    margin-bottom: 14px;
}
.result-link {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 44px;
    margin-top: 12px;
    border-radius: 12px;
    text-decoration: none !important;
    color: #FFFFFF !important;
    font-weight: 700;
    background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 100%);
    box-sizing: border-box;
}
.result-link:hover {
    filter: brightness(1.05);
}
.helper-copy {
    font-size: 13px;
    color: #AAB7CD;
    line-height: 1.8;
    margin-bottom: 12px;
}
.strategy-card {
    background: rgba(13,22,40,0.72);
    border: 1px solid rgba(148,163,184,0.10);
    border-radius: 16px;
    padding: 16px;
    min-height: 250px;
}
.strategy-label {
    font-size: 13px;
    color: #8FB0FF;
    font-weight: 700;
    margin-bottom: 10px;
}
.strategy-copy {
    font-size: 13px;
    color: #AAB7CD;
    line-height: 1.8;
    margin-top: 10px;
}
label, .stFileUploader label, .stTextInput label, .stTextArea label, .stSelectbox label {
    color: #D8E2F1 !important;
    font-weight: 600 !important;
}
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(148,163,184,0.16) !important;
    color: #F8FAFC !important;
    border-radius: 12px !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextInput"] input:active {
    background: transparent !important;
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    caret-color: #F8FAFC !important;
}
div[data-testid="stTextArea"] textarea,
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stTextArea"] textarea:active {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(148,163,184,0.16) !important;
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    caret-color: #F8FAFC !important;
    border-radius: 12px !important;
    line-height: 1.8 !important;
    min-height: 220px !important;
}
[data-testid="stTextInput"] > div,
[data-testid="stTextArea"] > div,
[data-baseweb="input"],
[data-baseweb="base-input"] {
    background: transparent !important;
}
input::placeholder, textarea::placeholder {
    color: #8FA3BF !important;
    -webkit-text-fill-color: #8FA3BF !important;
    opacity: 1 !important;
}
.stButton > button {
    border-radius: 12px !important;
    min-height: 44px !important;
}
button[kind="primary"] {
    background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 100%) !important;
    border: none !important;
}
button[kind="secondary"] {
    background: rgba(255,255,255,0.04) !important;
    color: #E5EDF8 !important;
    border: 1px solid rgba(148,163,184,0.16) !important;
}
[data-testid="stFileUploader"] section {
    background: rgba(255,255,255,0.04) !important;
    border: 1px dashed rgba(148,163,184,0.20) !important;
    border-radius: 14px !important;
}
</style>
""", unsafe_allow_html=True)


def get_dashscope_client():
    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        return None
    return OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )


def image_bytes_to_base64(image_bytes):
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image.thumbnail((1400, 1400))
    buf = BytesIO()
    image.save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def generate_need_from_image(image_bytes):
    client = get_dashscope_client()
    if client is None:
        raise ValueError("未检测到 DASHSCOPE_API_KEY，请先配置阿里云百炼 API Key。")

    image_b64 = image_bytes_to_base64(image_bytes)
    prompt = """
你是资深产品设计研究助手。
请根据这张原型图 / 界面图，输出一段适合设计研究使用的需求文案。

要求：
1. 用中文输出
2. 直接输出一段自然流畅的正文，不要分点，不要标题
3. 要说明这是一个什么类型的页面或系统
4. 要说明视觉风格、信息结构、关键交互重点
5. 要说明适合往哪些方向搜参考
6. 这段文案将直接填入“需求描述”输入框
"""
    resp = client.chat.completions.create(
        model="qwen-vl-plus",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }],
        temperature=0.4
    )
    return resp.choices[0].message.content.strip()


def analyze_need(text: str):
    text_lower = text.lower().strip()
    if not text_lower:
        return [], []

    keyword_pool = []
    notes = []

    def hit(words):
        return any(w in text_lower for w in words)

    if hit(["banner", "海报", "活动图", "运营图", "kv"]):
        keyword_pool.extend(["banner design", "marketing banner", "campaign hero section", "visual banner ui", "promotion landing page"])
        notes.append("当前需求更偏视觉表达、营销氛围和主视觉排版。")

    if hit(["b端", "后台", "企业", "管理端", "erp", "saas", "dashboard", "工作台", "平台"]):
        keyword_pool.extend(["enterprise dashboard", "admin panel", "saas platform", "b2b dashboard", "enterprise web app", "data table ui"])
        notes.append("当前需求更偏企业级后台、模块层级和信息组织。")

    if hit(["登录", "注册", "认证", "auth", "login", "sign in"]):
        keyword_pool.extend(["login page", "sign in page", "authentication flow", "auth screen", "enterprise login ui", "fintech auth screen"])
        notes.append("当前需求更偏表单、身份认证和信任感建立。")

    if hit(["支付", "结账", "checkout", "收银台", "付款", "billing"]):
        keyword_pool.extend(["payment flow", "checkout page", "billing page ui", "payment login", "fintech payment app", "payment confirmation page"])
        notes.append("当前需求更偏支付流程、关键确认节点和转化效率。")

    if hit(["首页", "首屏", "homepage", "landing"]):
        keyword_pool.extend(["homepage design", "landing page", "enterprise homepage", "saas homepage", "hero section ui"])
        notes.append("当前需求更偏首屏表达、品牌感和转化入口。")

    if hit(["移动端", "app", "mobile"]):
        keyword_pool.extend(["mobile app ui", "app design", "mobile dashboard", "mobile onboarding", "travel app design", "finance app ui"])
        notes.append("当前需求更偏移动端入口效率和核心操作路径。")

    if hit(["表单", "录入", "form", "input"]):
        keyword_pool.extend(["form design", "data entry ui", "enterprise form page", "input flow ui"])
        notes.append("当前需求更偏输入效率、字段层级和状态反馈。")

    if hit(["列表", "表格", "table", "list"]):
        keyword_pool.extend(["data table ui", "list page design", "enterprise table page", "dashboard list module"])
        notes.append("当前需求更偏数据阅读效率和筛选结构。")

    if not keyword_pool:
        keyword_pool.extend([text.strip(), f"{text.strip()} ui design", f"{text.strip()} web design", f"{text.strip()} app design", f"{text.strip()} interface"])
        notes.append("未命中特定规则，已生成通用搜索词。")

    dedup = []
    seen = set()
    for kw in keyword_pool:
        if kw not in seen:
            dedup.append(kw)
            seen.add(kw)

    return dedup[:10], notes


def build_search_strategy(need_text: str, keywords: list[str]):
    need = need_text.lower()
    first_round = keywords[:4]
    second_round = []
    alternates = []
    method = []

    if any(x in need for x in ["dashboard", "后台", "saas", "平台", "企业"]):
        second_round.extend(["dashboard overview", "enterprise workspace", "admin dashboard ui", "b2b platform homepage"])
        alternates.extend(["control center ui", "operations dashboard", "workbench design"])
        method.append("先用结构词建立完整参考框架，再补首页、表格、数据模块等细分方向。")

    if any(x in need for x in ["登录", "auth", "login", "sign in"]):
        second_round.extend(["login flow", "authentication page", "enterprise auth", "secure sign in ui"])
        alternates.extend(["identity verification ui", "2fa login page", "security onboarding"])
        method.append("先看基础登录页，再补看认证、异常提示、验证流程和安全感表达。")

    if any(x in need for x in ["支付", "billing", "checkout", "付款"]):
        second_round.extend(["checkout flow", "payment confirmation", "billing dashboard", "invoice page ui"])
        alternates.extend(["subscription billing ui", "fintech checkout", "payment status page"])
        method.append("先看主流程页，再补确认页、状态页和异常反馈页。")

    if any(x in need for x in ["banner", "visual", "marketing", "hero"]):
        second_round.extend(["campaign landing page", "hero banner design", "brand visual system"])
        alternates.extend(["promotion visual", "marketing page hero", "editorial layout ui"])
        method.append("先用主视觉词找方向，再补品牌词和版式词拉开结果差异。")

    if not second_round:
        second_round = keywords[4:8]

    if not alternates:
        alternates = ["modern interface design", "clean dashboard ui", "minimal product page"]

    if not method:
        method = ["先用更强结构词搜索，再补行业词、风格词和场景词，通常会得到更稳定的结果。"]

    return {
        "first_round": first_round[:4],
        "second_round": second_round[:4],
        "alternates": alternates[:4],
        "method": method[:3]
    }


def rank_platforms(need_text: str, keywords: list[str]):
    text = (need_text + " " + " ".join(keywords)).lower()

    def score_platform(name, base_reason):
        score = 0
        reasons = []

        if any(x in text for x in ["dashboard", "enterprise", "saas", "admin", "b2b", "platform"]):
            if name in ["Behance", "Dribbble", "站酷"]:
                score += 3
                reasons.append("当前需求偏系统化界面与后台场景。")

        if any(x in text for x in ["banner", "visual", "marketing", "campaign", "hero"]):
            if name in ["Pinterest", "花瓣", "小红书", "Dribbble"]:
                score += 3
                reasons.append("当前需求偏视觉表达与版式灵感。")

        if any(x in text for x in ["login", "auth", "sign in", "payment", "checkout", "billing"]):
            if name in ["Behance", "Dribbble", "站酷"]:
                score += 3
                reasons.append("当前需求偏关键流程页、表单和信任感设计。")

        if any(x in text for x in ["mobile", "app", "travel", "finance"]):
            if name in ["Behance", "Dribbble", "小红书"]:
                score += 2
                reasons.append("当前需求偏移动端场景和入口体验。")

        if any(x in text for x in ["homepage", "landing", "brand"]):
            if name in ["Behance", "Pinterest", "花瓣", "Dribbble"]:
                score += 2
                reasons.append("当前需求偏首屏表达和品牌呈现。")

        if any(x in text for x in ["中文", "本土", "运营", "活动", "品牌传播"]):
            if name in ["站酷", "花瓣", "小红书", "美叶"]:
                score += 2
                reasons.append("当前需求更适合补充中文语境与本土表达。")

        if not reasons:
            reasons.append(base_reason)

        extra = {
            "Behance": "适合先建立完整项目参考框架。",
            "Dribbble": "适合补充局部模块和视觉处理。",
            "站酷": "适合看中文语境下的案例表达。",
            "Pinterest": "适合发散氛围和版式方向。",
            "花瓣": "适合补中文视觉灵感与主视觉方向。",
            "小红书": "适合补近期流行表达和包装方式。",
            "美叶": "适合作为国内资源补充入口。"
        }

        return {
            "name": name,
            "score": score,
            "reason": "；".join(reasons[:2]) + " " + extra[name]
        }

    platforms = [
        score_platform("Behance", "适合看较完整的项目案例和成组展示。"),
        score_platform("Dribbble", "适合补充局部界面、局部视觉和高质量 shot。"),
        score_platform("Pinterest", "适合发散视觉方向、情绪和版式灵感。"),
        score_platform("花瓣", "适合补充中文视觉灵感和主视觉方向。"),
        score_platform("站酷", "适合观察中文设计语境与本土案例。"),
        score_platform("美叶", "适合作为国内设计资源与案例补充入口。"),
        score_platform("小红书", "适合观察近期流行表达和运营包装趋势。"),
    ]
    return sorted(platforms, key=lambda x: x["score"], reverse=True)


def generate_design_advice(need_text: str, keywords: list[str], platform_rankings: list[dict], strategy: dict):
    text = need_text.lower()
    advice = []

    if any(x in text for x in ["登录", "login", "auth", "sign in"]):
        advice.append("当前需求重点不只是登录入口本身，而是如何在第一屏建立信任感、减少输入负担，并让认证流程清晰可预期。建议重点观察表单层级、辅助说明、异常反馈、记住账号与二次验证的处理方式。")
    elif any(x in text for x in ["支付", "billing", "checkout", "付款"]):
        advice.append("当前需求核心是转化与安全感。建议不要只看视觉美观，更要拆解金额层级、信息确认、按钮状态、支付反馈和风险提示的呈现方式。")
    elif any(x in text for x in ["dashboard", "后台", "saas", "平台", "企业"]):
        advice.append("当前需求更偏企业级信息架构问题。建议重点观察首屏是否足够快地暴露核心任务、模块层级是否清晰、表格与卡片是否有明确优先级，以及筛选区是否压缩了用户理解成本。")
    else:
        advice.append("当前需求建议先拆成结构、视觉、交互、信任感/转化四层来观察，这样比只看风格更容易形成可落地的设计判断。")

    if strategy.get("first_round"):
        advice.append(f"建议首轮先用这些词建立主参考框架：{', '.join(strategy['first_round'])}。等基础方向稳定后，再用二轮词补充页面类型、模块细节和风格差异。")

    if platform_rankings:
        top3 = platform_rankings[:3]
        advice.append(f"平台使用上建议优先从 {top3[0]['name']} 开始，再用 {top3[1]['name']} 和 {top3[2]['name']} 做补充。前者更适合建立主参考框架，后两者更适合补局部表达、中文语境或视觉处理。")

    advice.append("建议不要只看竞品已有页面，也要主动拆解成熟产品在信息组织、状态反馈、表单效率和信任建立上的处理方式，再迁移到你当前需求中。")
    return advice[:4]


def search_behance_cards(keyword: str, limit: int = 9):
    search_url = f"https://www.behance.net/search/projects?search={quote(keyword)}"
    save_dir = "behance_shots_v4"
    os.makedirs(save_dir, exist_ok=True)

    items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1500, "height": 2200})
        page.goto(search_url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2500)

        for text in ["Accept", "接受", "Close", "关闭", "Not now", "以后再说"]:
            try:
                page.get_by_text(text, exact=False).first.click(timeout=400)
            except Exception:
                pass

        page.wait_for_timeout(1000)
        links = page.locator("a[href*='/gallery/']")
        count = links.count()
        seen = set()
        idx = 0

        for i in range(count):
            if idx >= limit:
                break

            link = links.nth(i)
            try:
                if not link.is_visible():
                    continue
            except Exception:
                continue

            try:
                href = link.get_attribute("href")
            except Exception:
                href = None

            if not href:
                continue

            if href.startswith("/"):
                href = f"https://www.behance.net{href}"

            if href in seen:
                continue
            seen.add(href)

            title = None
            try:
                title = link.get_attribute("title")
            except Exception:
                pass

            if not title:
                try:
                    txt = link.inner_text(timeout=800).strip()
                    if txt:
                        title = txt.split("\\n")[0].strip()
                except Exception:
                    pass

            if not title:
                title = f"Behance Result {idx + 1}"

            shot_path = os.path.join(save_dir, f"card_{idx + 1}.png")
            try:
                link.screenshot(path=shot_path)
            except Exception:
                page.screenshot(path=shot_path, full_page=False)

            items.append({
                "title": title,
                "href": href,
                "image": shot_path
            })
            idx += 1

        browser.close()

    return items


def fill_keyword(kw):
    st.session_state.search_keyword = kw


st.markdown('<div class="hero-title">Design Research Agent V4</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">这一版重点升级需求分析、搜索策略和平台推荐逻辑。系统不仅会给出关键词，还会告诉你应该先搜什么、为什么这样搜，以及不同平台分别适合补什么类型的参考。</div>',
    unsafe_allow_html=True
)
st.markdown(
    """
    <span class="pill">Prototype Upload</span>
    <span class="pill">AI Need Draft</span>
    <span class="pill">Search Strategy</span>
    <span class="pill">Platform Recommendation</span>
    <span class="pill">Behance Search</span>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <div class="top-status">
        <span class="top-dot"></span>
        <div class="top-status-text">DashScope Vision Ready · Search Strategy Ready · Platform Reasoning Ready</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="section-title">输入与需求生成</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sub">上传原型图后会自动识别并生成需求文案，你也可以继续手动补充或修改。</div>', unsafe_allow_html=True)

uploaded_image = st.file_uploader("上传原型图", type=["png", "jpg", "jpeg", "webp"])

if uploaded_image is not None:
    image_bytes = uploaded_image.getvalue()
    st.image(image_bytes, caption="已上传原型图", use_container_width=True)

    current_sig = f"{uploaded_image.name}_{uploaded_image.size}"
    if current_sig != st.session_state.last_upload_sig:
        try:
            with st.spinner("正在自动识别原型图并生成需求文案..."):
                draft_text = generate_need_from_image(image_bytes)
                st.session_state.need_text = draft_text
                st.session_state.last_upload_sig = current_sig
            st.success("已根据上传图片自动生成需求文案")
        except Exception as e:
            st.error("自动识别失败")
            st.code(str(e))

st.text_area(
    "需求描述",
    key="need_text",
    placeholder="例如：我想找企业级支付登录页参考，偏 SaaS 风格，希望页面既专业又有品牌信任感，表单结构清晰，适合 B 端产品场景。"
)

if st.button("分析需求并生成推荐", type="primary", use_container_width=True):
    keywords, notes = analyze_need(st.session_state.need_text)
    strategy = build_search_strategy(st.session_state.need_text, keywords)
    platforms = rank_platforms(st.session_state.need_text, keywords)
    advice = generate_design_advice(st.session_state.need_text, keywords, platforms, strategy)

    st.session_state.analysis_results = keywords
    st.session_state.need_judgement = notes
    st.session_state.search_strategy = strategy
    st.session_state.platform_rankings = platforms
    st.session_state.design_advice = advice

st.write("")
st.write("")
st.markdown('<div class="section-title">需求判断</div>', unsafe_allow_html=True)

if st.session_state.need_judgement:
    st.markdown('<div class="tip-list"><ul>', unsafe_allow_html=True)
    for note in st.session_state.need_judgement:
        st.markdown(f"<li>{note}</li>", unsafe_allow_html=True)
    st.markdown('</ul></div>', unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="empty-card">
        <div class="empty-title">等待需求分析</div>
        <div class="empty-sub">当你点击“分析需求并生成推荐”后，这里会展示系统对当前需求的初步判断。</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")
st.markdown('<div class="section-title">搜索策略</div>', unsafe_allow_html=True)

strategy = st.session_state.search_strategy
if strategy:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="strategy-label">首轮推荐词</div>', unsafe_allow_html=True)
        for kw in strategy.get("first_round", []):
            st.button(kw, key=f"first_{kw}", use_container_width=True, on_click=fill_keyword, args=(kw,))
        st.markdown('<div class="strategy-copy">先用结构更强的词建立主参考框架。</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="strategy-label">二轮补充词</div>', unsafe_allow_html=True)
        for kw in strategy.get("second_round", []):
            st.button(kw, key=f"second_{kw}", use_container_width=True, on_click=fill_keyword, args=(kw,))
        st.markdown('<div class="strategy-copy">用来补页面类型、模块细节和场景差异。</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="strategy-label">替代词 / 搜索方法</div>', unsafe_allow_html=True)
        for kw in strategy.get("alternates", []):
            st.button(kw, key=f"alt_{kw}", use_container_width=True, on_click=fill_keyword, args=(kw,))
        for line in strategy.get("method", []):
            st.markdown(f'<div class="strategy-copy">- {line}</div>', unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="empty-card">
        <div class="empty-title">等待搜索策略</div>
        <div class="empty-sub">系统会给出首轮推荐词、二轮补充词和替代词，而不是只给你一组静态关键词。</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")
st.markdown('<div class="section-title">设计建议</div>', unsafe_allow_html=True)

if st.session_state.design_advice:
    for advice in st.session_state.design_advice:
        st.markdown(f"""
        <div class="advice-card">
            <div class="advice-title">{advice}</div>
            <div class="advice-sub">基于当前需求描述、搜索策略与平台优先级生成</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
else:
    st.markdown("""
    <div class="empty-card">
        <div class="empty-title">等待设计建议</div>
        <div class="empty-sub">这里会展示更像设计研究助手的整体建议，而不是只做简单趋势总结。</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")
st.markdown('<div class="section-title">平台推荐</div>', unsafe_allow_html=True)

if st.session_state.platform_rankings:
    for row_start in range(0, len(st.session_state.platform_rankings), 3):
        row_items = st.session_state.platform_rankings[row_start:row_start + 3]
        row_cols = st.columns(3)
        for col_idx in range(3):
            with row_cols[col_idx]:
                if col_idx < len(row_items):
                    item = row_items[col_idx]
                    st.markdown(f"""
                    <div class="platform-card">
                        <div class="platform-rank">TOP {row_start + col_idx + 1}</div>
                        <div class="platform-name">{item['name']}</div>
                        <div class="platform-reason">{item['reason']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        st.write("")
else:
    st.markdown("""
    <div class="empty-card">
        <div class="empty-title">等待平台推荐</div>
        <div class="empty-sub">系统会根据需求特征和搜索关键词给出优先级建议，帮助你决定先从哪个平台开始找参考。</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")
st.markdown('<div class="section-title">Behance 搜索设置</div>', unsafe_allow_html=True)

search_left, search_right = st.columns([0.72, 0.28], gap="large")

with search_left:
    st.selectbox("当前展示平台", ["Behance"], index=0)
    st.text_input(
        "搜索关键词",
        key="search_keyword",
        placeholder="例如：enterprise homepage / login page / payment flow / saas platform"
    )
    st.markdown('<div class="section-sub">你可以手动输入，也可以点击上方搜索策略里的词自动填入这里。</div>', unsafe_allow_html=True)
    run_btn = st.button("开始搜索 · Behance 9-Card View", type="primary", use_container_width=True)

with search_right:
    m1, m2 = st.columns(2)
    with m1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">展示平台</div>
            <div class="metric-value">Behance</div>
            <div class="metric-sub">当前页图像展示已接通</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">结果规模</div>
            <div class="metric-value">9 Cards</div>
            <div class="metric-sub">九宫格参考浏览</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")
st.write("")
st.markdown('<div class="section-title">Behance 搜索结果</div>', unsafe_allow_html=True)

if run_btn:
    keyword = st.session_state.search_keyword
    if not keyword.strip():
        st.warning("请输入关键词或点击推荐关键词")
    else:
        with st.spinner("正在抓取 Behance 九宫格结果..."):
            try:
                items = search_behance_cards(keyword.strip(), limit=9)
                if items:
                    st.success("搜索完成")
                    for row_start in range(0, len(items), 3):
                        row_items = items[row_start:row_start + 3]
                        row_cols = st.columns(3)
                        for col_idx in range(3):
                            with row_cols[col_idx]:
                                if col_idx < len(row_items):
                                    item = row_items[col_idx]
                                    st.image(item["image"], use_container_width=True)
                                    st.markdown(
                                        f'<div class="result-card-title">{item["title"]}</div>',
                                        unsafe_allow_html=True
                                    )
                                    st.markdown(
                                        '<div class="result-card-meta">来源：Behance 搜索首屏截图</div>',
                                        unsafe_allow_html=True
                                    )
                                    st.markdown(
                                        f'<a class="result-link" href="{item["href"]}" target="_blank">打开 Behance 项目页</a>',
                                        unsafe_allow_html=True
                                    )
                        st.write("")
                else:
                    st.markdown("""
                    <div class="empty-card">
                        <div class="empty-title">未成功抓到首屏卡片</div>
                        <div class="empty-sub">请尝试更换英文关键词，或稍后再次执行搜索。</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error("运行失败")
                st.code(str(e))
else:
    st.markdown("""
    <div class="empty-card">
        <div class="empty-title">等待搜索</div>
        <div class="empty-sub">完成需求分析后，你可以点击推荐关键词自动填充搜索框，再执行 Behance 搜索。</div>
    </div>
    """, unsafe_allow_html=True)
