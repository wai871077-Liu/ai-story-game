import base64
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import streamlit as st


APP_TITLE = "重生之我该如何选择"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
ASSET_DIR = Path(__file__).parent / "assets"


@dataclass(frozen=True)
class Character:
    name: str
    role: str
    secret: str
    tone: str
    avatar: str


CHARACTERS = [
    Character(
        "小雨",
        "清冷坚韧的奖学金生，习惯把委屈藏在礼貌后面。",
        "她收到过一封匿名提醒，知道书吧储物柜里藏着关键录音。",
        "克制、敏感、偶尔露出柔软。",
        "xiaoyu.png",
    ),
    Character(
        "柳书昂",
        "文气温和的学生会骨干，擅长把锋芒藏进一句轻描淡写里。",
        "他看见过罗经理和学生会的人在雨夜交换文件袋。",
        "含蓄、聪明、话里有话。",
        "liu_shuang.png",
    ),
    Character(
        "徐佳珍",
        "小雨的好友，急性子，常把担心藏在吐槽后面。",
        "她手机里有一张模糊照片，拍到了真正的胁迫者。",
        "直率、紧张、护短。",
        "xu_jiazhen.png",
    ),
    Character(
        "管家老张",
        "公子家里的旧人，沉稳周到，永远提前半步出现。",
        "他受过老爷嘱托，要查清校园赞助资金流向。",
        "礼貌、稳重、暗中保护。",
        "lao_zhang.png",
    ),
    Character(
        "罗经理",
        "校企赞助方代表，笑容体面，手段并不体面。",
        "他正用代考把柄逼小雨签一份虚假证明。",
        "圆滑、压迫、总留退路。",
        "luo_manager.png",
    ),
]

CHARACTER_BY_NAME = {character.name: character for character in CHARACTERS}

SCENE_PRESETS = {
    "高中校园": {
        "asset": "scenes/high_school.png",
        "places": [
            "教学楼连廊，晚自习刚结束，操场灯光落在潮湿地砖上。",
            "高三楼下的公告栏旁，风把竞赛名单吹得轻轻作响。",
            "实验楼侧门，雨后的桂花香混着校服上淡淡的洗衣液味。",
        ],
        "mood": "青春、重生、校园选择、暗线调查",
    },
    "公司办公室": {
        "asset": "scenes/office.png",
        "places": [
            "集团顶层会议室，城市夜景贴在玻璃幕墙外。",
            "总裁办外的长廊，打印机吐出一份没有署名的合同。",
            "深夜茶水间，咖啡机嗡鸣声盖住了远处压低的争执。",
        ],
        "mood": "职场、权力、利益博弈、暧昧试探",
    },
    "别墅": {
        "asset": "scenes/villa.png",
        "places": [
            "雨夜别墅的玻璃花房，壁灯把玫瑰影子拉得很长。",
            "二楼书房，檀木桌上压着一封没有寄出的信。",
            "庭院回廊，远处车灯扫过湿亮的石阶。",
        ],
        "mood": "豪门、秘密、旧账、命运选择",
    },
}

APPEARANCES = {
    "深色": {
        "app_bg": "#070b14",
        "scrim": "linear-gradient(rgba(4,8,18,.42), rgba(4,8,18,.78))",
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
        "scrim": "linear-gradient(rgba(246,248,252,.84), rgba(246,248,252,.94))",
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


def image_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def avatar_uri(name: str) -> str:
    character = CHARACTER_BY_NAME.get(name)
    if not character:
        return ""
    return image_data_uri(ASSET_DIR / "avatars" / character.avatar)


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
    st.session_state.setdefault("scene", "高中校园")
    st.session_state.setdefault("tone", "暧昧试探")
    st.session_state.setdefault("memory_bank", [])
    st.session_state.setdefault("active_memory", "")
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
    scene = st.session_state.get("scene", "高中校园")
    place = random.choice(SCENE_PRESETS[scene]["places"])
    return (
        f"场景记录：{place}\n\n"
        "重生后的第一天，你终于回到那个决定命运的岔路口。小雨抱着资料从转角出现，"
        "罗经理靠在栏杆边，手里的文件袋被捏出折痕。柳书昂站在阴影里没有说话，"
        "徐佳珍一路小跑，而管家老张已经把伞递到了你的手边。\n\n"
        "这一次，你知道每个人都藏着秘密，但你还不知道该相信谁。"
    )


def css() -> None:
    appearance = APPEARANCES[st.session_state.appearance]
    scene = SCENE_PRESETS[st.session_state.scene]
    bg_uri = image_data_uri(ASSET_DIR / scene["asset"])
    bg_layer = f"url('{bg_uri}') center / cover no-repeat fixed," if bg_uri else ""

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
            background:
                {appearance["scrim"]},
                {bg_layer}
                var(--app-bg);
            color: var(--text);
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
        [data-testid="stChatMessage"] {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 22px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(22px) saturate(140%);
        }}
        [data-testid="stChatMessage"] p {{
            color: var(--text);
            font-size: 1.02rem;
            line-height: 1.85;
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
        .stChatInput textarea {{
            border-radius: 20px;
            background: var(--input) !important;
            color: var(--text) !important;
            border: 1px solid var(--border);
        }}
        .stChatInput textarea::placeholder {{
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
            border-radius: 24px;
            padding: 18px;
            margin: 8px 0 18px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(24px) saturate(150%);
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
            display: grid;
            grid-template-columns: 48px 1fr;
            gap: 12px;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
        }}
        .character-row:last-child {{ border-bottom: none; }}
        .character-row img {{
            width: 48px;
            height: 48px;
            object-fit: cover;
            border-radius: 16px;
            border: 1px solid var(--border);
        }}
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
        @media (max-width: 720px) {{
            .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}
            [data-testid="column"] {{
                width: 100% !important;
                flex: 1 1 100% !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def system_prompt() -> str:
    roles = "\n".join(
        f"- {c.name}: {c.role} 秘密: {c.secret} 语气: {c.tone}" for c in CHARACTERS
    )
    memories = "；".join(st.session_state.memory_bank[-8:]) or "暂无长期记忆。"
    if st.session_state.active_memory:
        memories += f"；当前唤醒记忆：{st.session_state.active_memory}"
    scene = st.session_state.scene
    return f"""
你是中文互动剧情游戏《{APP_TITLE}》的叙事引擎。
玩家身份是“公子”，在重生后重新面对关键选择。

写作要求：
- 输出 180 到 260 字。
- 当前场景类型：{scene}。氛围：{SCENE_PRESETS[scene]["mood"]}。
- 每次至少让一个角色对玩家行动做出具体反应。
- 不要替玩家做最终决定。
- 结尾留下一个可继续输入的钩子。
- 可含动作描写，但不要输出系统解释。
- 当前叙事语气：{st.session_state.tone}

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
        role = "assistant" if msg["speaker"] != "公子" else "user"
        messages.append({"role": role, "content": f'{msg["speaker"]}: {msg["text"]}'})
    messages.append({"role": "user", "content": f"公子: {player_text}"})

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
    focus = random.choice(CHARACTERS)
    scene = random.choice(
        [
            "远处忽然掠过一束光，玻璃上映出几个人影。",
            "广播短促地响了一声，又像被人突然切断。",
            "走廊尽头传来脚步声，节奏很轻，却每一步都停得刚刚好。",
            "文件袋里露出半张收据，抬头正是赞助项目。",
        ]
    )
    reactions = [
        f"{focus.name}听完你的话，眼神明显停了一下。这个名字像被风吹过水面，露出一点藏不住的波纹。",
        f"{focus.name}抬头看你，像是在判断这句话里有几分真心，又有几分试探。",
        f"{focus.name}轻轻吸了口气，声音压低：公子，你现在插手，就等于告诉他们你已经知道了。",
    ]
    twist = random.choice(
        [
            "徐佳珍忽然把手机屏幕扣在胸口，屏幕上似乎是一张模糊照片。",
            "管家老张往前半步，替你挡住了罗经理投来的视线。",
            "柳书昂袖口露出一截折起的名单，像早就等着你发现。",
            "小雨的耳尖微红，却没有后退，像终于等到有人站到她这边。",
        ]
    )
    return (
        f"{scene}\n\n"
        f"你说：“{player_text}”\n\n"
        f"{random.choice(reactions)} {twist} 罗经理笑了笑，指尖敲着文件袋："
        "既然公子也在，不如一起听听这份证明该怎么写。\n\n"
        "空气安静下来，所有人的目光都落在你身上。"
    )


def add_player_message(text: str) -> None:
    st.session_state.messages.append({"speaker": "公子", "kind": "player", "text": text})
    try:
        answer, mode = deepseek_generate(text)
    except Exception as exc:
        answer = offline_generate(text) + f"\n\n（DeepSeek 调用失败，已切换离线剧情：{exc}）"
        mode = "offline"
    st.session_state.messages.append(
        {"speaker": "剧情引擎" if mode == "deepseek" else "离线引擎", "kind": "ai", "text": answer}
    )


def auto_advance() -> None:
    prompts = [
        "我看向小雨，示意她先别急，把今晚看到的一切从头说。",
        "我让老张去查文件袋来源，同时请柳书昂留下来作证。",
        "我故意对罗经理笑了笑，问他是不是还有另一份合同。",
        "我把伞递给小雨，低声告诉她，这一次我会先选她。",
    ]
    add_player_message(random.choice(prompts))


def reset_story() -> None:
    for key in ["messages", "memory_bank", "active_memory"]:
        st.session_state.pop(key, None)
    init_state()


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
            "你记得柳书昂曾在最后一刻提醒你：真正的证据不在明处。",
        ]
        st.session_state.active_memory = random.choice(seeds)
        st.session_state.memory_bank.append(st.session_state.active_memory)


def render_message(message: dict[str, str]) -> None:
    avatar = avatar_uri(message["speaker"]) or {"narrator": "🧭", "player": "🎭", "ai": "✦"}.get(
        message["kind"], "💬"
    )
    with st.chat_message(message["speaker"], avatar=avatar):
        st.markdown(message["text"])


def render_character_cards() -> None:
    for character in CHARACTERS:
        uri = image_data_uri(ASSET_DIR / "avatars" / character.avatar)
        st.markdown(
            f"""
            <div class="character-row">
                <img src="{uri}" alt="{character.name}">
                <div>
                    <div class="character-name">{character.name}</div>
                    <div class="character-role">{character.role}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_control_panel() -> None:
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">外观与场景</div>', unsafe_allow_html=True)
    scene_col, appearance_col, tone_col = st.columns([1.2, 1, 1.1])
    with scene_col:
        st.session_state.scene = st.segmented_control(
            "画面背景",
            list(SCENE_PRESETS),
            selection_mode="single",
            default=st.session_state.scene,
        )
    with appearance_col:
        st.session_state.appearance = st.segmented_control(
            "外观",
            ["深色", "浅色"],
            selection_mode="single",
            default=st.session_state.appearance,
        )
    with tone_col:
        st.session_state.tone = st.selectbox(
            "叙事语气",
            ["暧昧试探", "悬疑推进", "温柔守护", "强势摊牌"],
            index=["暧昧试探", "悬疑推进", "温柔守护", "强势摊牌"].index(st.session_state.tone),
        )
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="✦", layout="wide")
    init_state()
    css()

    st.title(APP_TITLE)
    engine = "DeepSeek 在线" if deepseek_key() else "离线剧情引擎"
    st.markdown(
        f'<div class="status">当前引擎：{engine} · 场景：{st.session_state.scene} · 外观：{st.session_state.appearance}</div>',
        unsafe_allow_html=True,
    )

    render_control_panel()

    for message in st.session_state.messages:
        render_message(message)

    left, mid, mem, role = st.columns([1.0, 1.15, 1.5, 1.45])
    with left:
        if st.button("✦ 新剧情", use_container_width=True):
            reset_story()
            st.rerun()
    with mid:
        if st.button("🤖 自动推进剧情", use_container_width=True):
            auto_advance()
            st.rerun()
    with mem:
        with st.expander("💾 封存 / 唤醒记忆"):
            a, b = st.columns(2)
            with a:
                if st.button("封存最近一幕", use_container_width=True):
                    save_memory()
                    st.rerun()
            with b:
                if st.button("唤醒记忆", use_container_width=True):
                    awaken_memory()
                    st.rerun()
            if st.session_state.active_memory:
                st.markdown(f'<span class="pill">已唤醒：{st.session_state.active_memory}</span>', unsafe_allow_html=True)
            if st.session_state.memory_bank:
                for item in st.session_state.memory_bank[-8:]:
                    st.markdown(f'<span class="pill">{item}</span>', unsafe_allow_html=True)
            else:
                st.caption("还没有文件也可以唤醒，系统会先生成一条前世记忆。")
    with role:
        with st.expander("📜 角色背景"):
            render_character_cards()

    prompt = st.chat_input("公子，请指示...")
    if prompt:
        add_player_message(prompt)
        st.rerun()


if __name__ == "__main__":
    main()
