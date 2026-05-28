import html
import json
import os
import random
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
import streamlit as st


APP_TITLE = "重生之我该如何选择"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
SAVE_VERSION = 1


@dataclass(frozen=True)
class Character:
    name: str
    role: str
    secret: str
    style: str


CHARACTERS = [
    Character(
        "小雨",
        "女主，清冷坚韧的优等生。她把委屈藏在礼貌后面，最难相信别人，也最容易被真诚打动。",
        "她收到过一封匿名提醒，知道罗经理正在借一份文件制造污名。",
        "克制、敏感、偶尔露出柔软。",
    ),
    Character(
        "柳书昂",
        "玩家扮演的主人公。重生后，他必须重新选择如何保护小雨，并赢得她的爱。",
        "他记得前世错过小雨的结局，因此这一次不想再沉默。",
        "由玩家输入决定，不替玩家做决定。",
    ),
    Character(
        "徐佳珍",
        "小雨身边的同学，非常嫉妒小雨的学习成绩，同时暗恋柳书昂。",
        "她故意把一些流言推向小雨，但又害怕柳书昂真的讨厌自己。",
        "酸涩、敏感、嘴硬，容易失控。",
    ),
    Character(
        "管家老张",
        "柳家旧人，沉稳周到，永远提前半步出现。",
        "他受过老爷嘱托，要查清校园赞助资金流向。",
        "礼貌、稳重、暗中保护。",
    ),
    Character(
        "罗经理",
        "反派角色，校企赞助方代表。笑容体面，手段并不体面。",
        "他正用伪造的把柄逼小雨签一份虚假证明，同时试图拿柳书昂当筹码。",
        "圆滑、压迫、总留退路。",
    ),
]

PLACES = [
    "教学楼连廊，晚自习刚结束，操场灯光落在潮湿地砖上。",
    "高三楼下的公告栏旁，风把竞赛名单吹得轻轻作响。",
    "实验楼侧门，雨后的桂花香混着校服上淡淡的洗衣液味。",
]

APPEARANCES = {
    "深色": {
        "app_bg": "#070b14",
        "surface": "rgba(20, 28, 44, .74)",
        "surface_strong": "rgba(18, 25, 40, .9)",
        "border": "rgba(255,255,255,.16)",
        "text": "#f7f1e6",
        "muted": "rgba(247,241,230,.68)",
        "accent": "#f5c35b",
        "button_text": "#16120a",
        "input": "rgba(22, 31, 49, .94)",
        "shadow": "0 24px 70px rgba(0,0,0,.42)",
    },
    "浅色": {
        "app_bg": "#f5f7fb",
        "surface": "rgba(255, 255, 255, .82)",
        "surface_strong": "rgba(255, 255, 255, .96)",
        "border": "rgba(20,31,48,.14)",
        "text": "#172033",
        "muted": "rgba(23,32,51,.62)",
        "accent": "#3478f6",
        "button_text": "#ffffff",
        "input": "rgba(255,255,255,.96)",
        "shadow": "0 24px 70px rgba(31,45,76,.18)",
    },
}


def deepseek_key() -> str:
    try:
        key = st.secrets.get("DEEPSEEK_API_KEY", "")
    except Exception:
        key = ""
    return key or os.getenv("DEEPSEEK_API_KEY", "")


def deepseek_model() -> str:
    try:
        model = st.secrets.get("DEEPSEEK_MODEL", "")
    except Exception:
        model = ""
    return model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def init_state() -> None:
    st.session_state.setdefault("appearance", "深色")
    st.session_state.setdefault("memory_bank", [])
    st.session_state.setdefault("active_memory", "")
    st.session_state.setdefault("affection", 0)
    st.session_state.setdefault(
        "messages",
        [
            {
                "speaker": "旁白",
                "kind": "narrator",
                "text": opening_scene(),
            }
        ],
    )


def opening_scene() -> str:
    place = random.choice(PLACES)
    return (
        f"场景记录：{place}\n\n"
        "重生后的第一天，柳书昂终于回到那个决定命运的岔路口。小雨抱着资料从转角出现，"
        "罗经理靠在栏杆边，手里的文件袋被捏出折痕。徐佳珍站在不远处盯着小雨，"
        "眼神里藏着嫉妒和不甘，而管家老张已经把伞递到了柳书昂手边。\n\n"
        "这一次，柳书昂的目标很明确：保护小雨，靠近小雨，最终让她愿意把手交给自己。"
    )


def css() -> None:
    appearance = APPEARANCES[st.session_state.appearance]

    st.markdown(
        f"""
        <style>
        :root {{
            --app-bg: {appearance["app_bg"]};
            --surface: {appearance["surface"]};
            --surface-strong: {appearance["surface_strong"]};
            --border: {appearance["border"]};
            --text: {appearance["text"]};
            --muted: {appearance["muted"]};
            --accent: {appearance["accent"]};
            --button-text: {appearance["button_text"]};
            --input: {appearance["input"]};
            --shadow: {appearance["shadow"]};
        }}
        .stApp {{
            background: var(--app-bg);
            color: var(--text);
        }}
        header,
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="manage-app-button"],
        [data-testid="stStatusWidget"],
        [data-testid="appCreatorAvatar"],
        a:has([data-testid="appCreatorAvatar"]),
        [class*="profileContainer"],
        [class*="viewerBadge"],
        #MainMenu,
        footer {{
            display: none !important;
            visibility: hidden !important;
        }}
        .block-container {{
            max-width: 1080px;
            padding-top: 2rem;
            padding-bottom: 7rem;
        }}
        h1 {{
            color: var(--text) !important;
            font-size: clamp(2rem, 4vw, 3.4rem) !important;
            letter-spacing: 0 !important;
            line-height: 1.08 !important;
            text-shadow: 0 10px 34px rgba(0, 0, 0, .18);
        }}
        .dialogue-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(22px) saturate(140%);
            padding: 20px 24px;
            margin: 14px 0;
        }}
        .dialogue-speaker {{
            color: var(--muted);
            font-size: .86rem;
            font-weight: 800;
            margin-bottom: 9px;
        }}
        .dialogue-text {{
            color: var(--text);
            font-size: 1.02rem;
            line-height: 1.85;
        }}
        .dialogue-aside {{
            color: var(--muted);
            font-style: italic;
        }}
        .dialogue-line {{
            display: block;
            margin: 0 0 10px;
        }}
        .dialogue-line:last-child {{
            margin-bottom: 0;
        }}
        .stButton > button {{
            min-height: 3rem;
            border-radius: 16px;
            border: 1px solid var(--border);
            background: linear-gradient(180deg, color-mix(in srgb, var(--accent), white 18%), var(--accent));
            color: var(--button-text);
            font-weight: 700;
            box-shadow: 0 12px 30px rgba(0,0,0,.14);
        }}
        .stButton > button:hover {{
            border-color: color-mix(in srgb, var(--accent), white 30%);
            transform: translateY(-1px);
        }}
        .stExpander {{
            border-radius: 18px !important;
            background: var(--surface);
            border: 1px solid var(--border);
            backdrop-filter: blur(18px) saturate(140%);
        }}
        textarea {{
            border-radius: 20px;
            background: var(--input) !important;
            color: var(--text) !important;
            border: 1px solid var(--border);
        }}
        textarea::placeholder {{
            color: var(--muted) !important;
        }}
        .status {{
            color: var(--muted);
            margin-top: -.45rem;
            margin-bottom: 1.2rem;
            font-size: .96rem;
        }}
        .control-panel {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px;
            margin: 8px 0 18px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(24px) saturate(150%);
        }}
        .affection-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(24px) saturate(150%);
            margin: 8px 0 18px;
            position: sticky;
            top: 24px;
            z-index: 3;
        }}
        .affection-title {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: var(--text);
            font-weight: 800;
            margin-bottom: 10px;
        }}
        .affection-track {{
            height: 12px;
            border-radius: 999px;
            overflow: hidden;
            background: color-mix(in srgb, var(--surface-strong), black 7%);
            border: 1px solid var(--border);
        }}
        .affection-fill {{
            height: 100%;
            width: var(--affection);
            background: linear-gradient(90deg, #ff6f91, #ff9fbc);
            border-radius: inherit;
        }}
        .affection-note {{
            color: var(--muted);
            font-size: .88rem;
            margin-top: 9px;
            line-height: 1.45;
        }}
        .section-title {{
            color: var(--muted);
            font-size: .78rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .pill {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            margin: 0 8px 8px 0;
            padding: 7px 11px;
            border: 1px solid var(--border);
            border-radius: 999px;
            color: var(--text);
            background: color-mix(in srgb, var(--surface-strong), transparent 18%);
            font-size: 13px;
        }}
        .character-row {{
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
        }}
        .character-row:last-child {{ border-bottom: none; }}
        .character-name {{
            font-weight: 800;
            color: var(--text);
            margin-bottom: 2px;
        }}
        .character-role {{
            color: var(--muted);
            font-size: .9rem;
            line-height: 1.45;
        }}
        div[data-testid="stRadio"] label, div[data-testid="stSelectbox"] label {{
            color: var(--muted) !important;
        }}
        div[data-testid="stRadio"] p {{
            color: var(--text) !important;
        }}
        div[data-testid="stRadio"] > label {{
            display: none;
        }}
        @media (max-width: 720px) {{
            .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}
            [data-testid="column"] {{
                width: 100% !important;
                flex: 1 1 100% !important;
            }}
            .affection-card {{
                position: static;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def system_prompt() -> str:
    roles = "\n".join(
        f"- {c.name}: {c.role} 秘密: {c.secret} 表现风格: {c.style}" for c in CHARACTERS
    )
    memories = "；".join(st.session_state.memory_bank[-8:]) or "暂无长期记忆。"
    if st.session_state.active_memory:
        memories += f"；当前唤醒记忆：{st.session_state.active_memory}"
    return f"""
你是中文互动剧情游戏《{APP_TITLE}》的叙事引擎。
玩家身份是“柳书昂”，重生后重新面对关键选择。
玩家目标：获得女主“小雨”的爱，并最终和小雨在一起。
当前小雨心动指数：{st.session_state.affection}%。

写作要求：
- 输出 180 到 260 字。
- 整体氛围：青春校园、重生选择、恋爱攻略、暗线调查。
- 重点描写小雨对柳书昂行动的反应；罗经理是反派，徐佳珍嫉妒小雨且暗恋柳书昂。
- 不要替玩家做最终决定。
- 结尾留下一个可继续输入的钩子。
- 严格使用恋爱游戏对话格式：括号里面写心理活动、动作、环境提示；括号外写角色真正说出口的话。
- 示例：小雨：（她攥紧书角，眼神躲开了一瞬）柳书昂，你为什么突然帮我？
- 不要输出系统解释，不要用项目符号。

角色设定：
{roles}

已封存/唤醒记忆：
{memories}
""".strip()


def deepseek_generate(player_text: str) -> tuple[str, str]:
    api_key = deepseek_key()
    if not api_key:
        return offline_generate(player_text), "offline"

    recent = st.session_state.messages[-8:]
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt()}]
    for msg in recent:
        role = "user" if msg["speaker"] == "柳书昂" else "assistant"
        messages.append({"role": role, "content": f'{msg["speaker"]}: {msg["text"]}'})
    messages.append({"role": "user", "content": f"柳书昂: {player_text}"})

    response = requests.post(
        DEEPSEEK_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": deepseek_model(),
            "messages": messages,
            "temperature": 0.88,
            "max_tokens": 520,
        },
        timeout=45,
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    return data["choices"][0]["message"]["content"].strip(), "deepseek"


def offline_generate(player_text: str) -> str:
    scene = random.choice(
        [
            "远处忽然掠过一束光，玻璃上映出几个人影。",
            "广播短促地响了一声，又像被人突然切断。",
            "走廊尽头传来脚步声，节奏很轻，却每一步都停得刚刚好。",
            "文件袋里露出半张收据，抬头正是赞助项目。",
        ]
    )
    twist = random.choice(
        [
            "徐佳珍：（她把手机扣在胸口，眼神从小雨身上移到你脸上）柳书昂，你就这么相信她吗？",
            "管家老张：（他往前半步，替你挡住罗经理投来的视线）少爷，罗经理手里的文件，恐怕不干净。",
            "罗经理：（他笑意不达眼底，指尖敲着文件袋）柳同学，年轻人别把同情错当喜欢。",
        ]
    )
    return (
        f"{scene}\n\n"
        f"柳书昂：（你向前一步，声音压得很稳）{player_text}\n\n"
        "小雨：（她抱紧书本，睫毛轻轻颤了一下，像是不敢立刻相信你）"
        "柳书昂，你为什么……突然站在我这边？\n\n"
        f"{twist}\n\n"
        "小雨：（她终于抬头看你，眼底的防备松动了一点）如果你真的知道些什么，就别只说一半。"
    )


def add_player_message(text: str) -> None:
    st.session_state.messages.append({"speaker": "柳书昂", "kind": "player", "text": text})
    try:
        answer, mode = deepseek_generate(text)
    except Exception as exc:
        answer = offline_generate(text) + f"\n\n（DeepSeek 调用失败，已切换离线剧情：{exc}）"
        mode = "offline"
    st.session_state.messages.append(
        {"speaker": "剧情引擎" if mode == "deepseek" else "离线引擎", "kind": "ai", "text": answer}
    )
    update_affection(text, answer)


def update_affection(player_text: str, answer: str) -> None:
    text = f"{player_text} {answer}"
    positive_words = ["保护", "相信", "陪", "解释", "道歉", "真相", "小雨", "选择你", "站在你", "别怕", "我在"]
    negative_words = ["威胁", "命令", "利用", "闭嘴", "交易", "罗经理说得对", "算了", "怀疑你"]
    delta = 2
    delta += sum(2 for word in positive_words if word in text)
    delta -= sum(4 for word in negative_words if word in text)
    if "徐佳珍" in text and "小雨" not in text:
        delta -= 2
    st.session_state.affection = max(0, min(100, st.session_state.affection + delta))


def auto_advance() -> None:
    prompts = [
        "我看向小雨，示意她先别急，把今晚看到的一切从头说。",
        "我让老张去查文件袋来源，同时请小雨先相信我一次。",
        "我故意对罗经理笑了笑，问他是不是还有另一份合同。",
        "我把伞递给小雨，低声告诉她，这一次我会先选她。",
    ]
    add_player_message(random.choice(prompts))


def reset_story() -> None:
    for key in ["messages", "memory_bank", "active_memory", "affection"]:
        st.session_state.pop(key, None)
    init_state()


def memory_file_name() -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"xiaoyu-memory-{timestamp}.json"


def build_memory_file() -> str:
    data = {
        "version": SAVE_VERSION,
        "title": APP_TITLE,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "appearance": st.session_state.appearance,
        "affection": st.session_state.affection,
        "messages": st.session_state.messages,
        "memory_bank": st.session_state.memory_bank,
        "active_memory": st.session_state.active_memory,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def restore_memory_file(uploaded_file: Any) -> tuple[bool, str]:
    try:
        data = json.loads(uploaded_file.getvalue().decode("utf-8"))
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        return False, "这个文件不是有效的记忆文件。"

    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        return False, "记忆文件里没有可恢复的对话记录。"
    for message in messages:
        if not isinstance(message, dict):
            return False, "记忆文件里的对话格式不正确。"
        if not all(isinstance(message.get(key), str) for key in ("speaker", "kind", "text")):
            return False, "记忆文件里的对话缺少必要字段。"

    try:
        affection = int(data.get("affection", 0))
    except (TypeError, ValueError):
        affection = 0

    st.session_state.messages = messages
    st.session_state.affection = max(0, min(100, affection))
    st.session_state.memory_bank = [
        str(item) for item in data.get("memory_bank", []) if isinstance(item, str)
    ][-12:]
    st.session_state.active_memory = str(data.get("active_memory", ""))
    if data.get("appearance") in APPEARANCES:
        st.session_state.appearance = data["appearance"]

    last_ai = next((m["text"] for m in reversed(messages) if m["kind"] == "ai"), "")
    if last_ai and not st.session_state.active_memory:
        st.session_state.active_memory = last_ai.split("\n")[0][:120]
    return True, "已唤醒这份记忆，可以继续上一次的回忆来游戏。"


def save_memory() -> None:
    recent_ai = [m["text"] for m in st.session_state.messages if m["kind"] == "ai"]
    if recent_ai:
        snippet = recent_ai[-1].split("\n")[0][:80]
        st.session_state.memory_bank.append(snippet)


def awaken_memory() -> None:
    if st.session_state.memory_bank:
        st.session_state.active_memory = random.choice(st.session_state.memory_bank)
    else:
        seeds = [
            "你记得前世的雨夜里，小雨没有等到解释的机会。",
            "你记得罗经理的文件袋里不只有合同，还有一张被折过的照片。",
            "你记得徐佳珍曾经哭着说：为什么你眼里永远只有小雨。",
        ]
        st.session_state.active_memory = random.choice(seeds)
        st.session_state.memory_bank.append(st.session_state.active_memory)


def format_dialogue_html(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"（([^（）]+)）", r'<span class="dialogue-aside">（\1）</span>', escaped)
    lines = escaped.splitlines()
    rendered_lines = [
        f'<span class="dialogue-line">{line}</span>' if line else '<span class="dialogue-line"></span>'
        for line in lines
    ]
    return "".join(rendered_lines)


def render_message(message: dict[str, str]) -> None:
    speaker = html.escape(message["speaker"])
    text = format_dialogue_html(message["text"])
    st.markdown(
        f"""
        <div class="dialogue-card">
            <div class="dialogue-speaker">{speaker}</div>
            <div class="dialogue-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_character_cards() -> None:
    for character in CHARACTERS:
        st.markdown(
            f"""
            <div class="character-row">
                <div class="character-name">{character.name}</div>
                <div class="character-role">{character.role}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_control_panel() -> None:
    st.markdown('<div class="section-title">外观</div>', unsafe_allow_html=True)
    st.radio(
        "外观",
        ["深色", "浅色"],
        key="appearance",
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown(
        f'<span class="pill">当前外观：{st.session_state.appearance}</span>',
        unsafe_allow_html=True,
    )


def render_affection_card() -> None:
    affection = st.session_state.affection
    st.markdown(
        f"""
        <div class="affection-card">
            <div class="affection-title"><span>小雨心动指数</span><span>{affection}%</span></div>
            <div class="affection-track"><div class="affection-fill" style="--affection: {affection}%;"></div></div>
            <div class="affection-note">根据柳书昂每次对小雨的态度、选择和表达实时变化。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_memory_panel() -> None:
    with st.expander("存储 / 唤醒记忆", expanded=True):
        st.download_button(
            "存储当前对话为记忆文件",
            data=build_memory_file(),
            file_name=memory_file_name(),
            mime="application/json",
            use_container_width=True,
        )
        uploaded_file = st.file_uploader(
            "选择之前存储的记忆文件",
            type=["json"],
            accept_multiple_files=False,
        )
        if st.button("唤醒记忆并继续", use_container_width=True):
            if uploaded_file is None:
                st.warning("请先选择一个之前存储的记忆文件。")
            else:
                restored, message = restore_memory_file(uploaded_file)
                if restored:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)


def render_player_input() -> None:
    with st.form("player_input", clear_on_submit=True):
        text = st.text_area(
            "柳书昂的行动或对白",
            placeholder="柳书昂，请输入你的行动或对白...",
            height=90,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("发送", use_container_width=True)
    if submitted and text.strip():
        add_player_message(text.strip())
        st.rerun()


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="✦", layout="wide")
    init_state()
    css()

    st.title(APP_TITLE)

    story_col, affection_col = st.columns([3, 1], gap="large")
    with story_col:
        render_control_panel()
        render_memory_panel()

        for message in st.session_state.messages:
            render_message(message)

        render_player_input()
    with affection_col:
        render_affection_card()


if __name__ == "__main__":
    main()
