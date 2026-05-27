import base64
import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import streamlit as st


DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
ASSET_DIR = Path(__file__).parent / "assets"


@dataclass(frozen=True)
class Character:
    name: str
    role: str
    secret: str
    tone: str


CHARACTERS = [
    Character(
        "林雪",
        "清冷坚韧的奖学金生，正在被一桩代考风波牵连。",
        "她收到过一封匿名提醒，知道书吧储物柜里藏着关键录音。",
        "克制、敏感、偶尔露出柔软。",
    ),
    Character(
        "沈清",
        "古筝社主力，温和疏离，像什么都知道却从不明说。",
        "她看见过李经理和学生会的人在雨夜交换文件袋。",
        "含蓄、聪明、话里有话。",
    ),
    Character(
        "赵雅",
        "林雪的室友，急性子，常把担心藏在吐槽后面。",
        "她手机里有一张模糊照片，拍到了真正的胁迫者。",
        "直率、紧张、护短。",
    ),
    Character(
        "管家老张",
        "公子家里的旧人，沉稳周到，永远提前半步出现。",
        "他受过老爷嘱托，要查清校园赞助资金流向。",
        "礼貌、稳重、暗中保护。",
    ),
    Character(
        "李经理",
        "校企赞助方代表，笑容体面，手段并不体面。",
        "他正用代考把柄逼林雪签一份虚假证明。",
        "圆滑、压迫、总留退路。",
    ),
]

SCENES = [
    "学生活动中心二楼书吧，窗外刚下过雨，路灯在积水里晕成金色。",
    "旧图书馆西侧回廊，风把公告栏上的失物招领吹得哗哗作响。",
    "音乐楼后的银杏道，琴房灯光一盏盏熄灭，只剩远处保安亭的蓝光。",
    "校门口的黑色轿车旁，空气里有潮湿柏油和冷掉咖啡的味道。",
]

THEMES = {
    "月夜": {
        "bg": "linear-gradient(135deg, #101426 0%, #132744 56%, #111827 100%)",
        "accent": "#d9aa38",
        "panel": "rgba(24, 36, 58, 0.78)",
        "text": "#f7ecd2",
    },
    "雨灯": {
        "bg": "linear-gradient(135deg, #13201d 0%, #26392e 58%, #0d171c 100%)",
        "accent": "#c7dd7a",
        "panel": "rgba(20, 35, 31, 0.78)",
        "text": "#f1f4dd",
    },
    "暗金": {
        "bg": "linear-gradient(135deg, #1b1520 0%, #342230 54%, #15121a 100%)",
        "accent": "#e2b66b",
        "panel": "rgba(44, 31, 43, 0.8)",
        "text": "#f8ead4",
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
    st.session_state.setdefault("theme", "月夜")
    st.session_state.setdefault("tone", "暧昧试探")
    st.session_state.setdefault("memory_bank", [])
    st.session_state.setdefault(
        "messages",
        [
            {
                "speaker": "旁白",
                "kind": "narrator",
                "text": (
                    f"场景记录：{random.choice(SCENES)}\n\n"
                    "林雪抱着书从楼梯转角出现，肩头还沾着雨珠。李经理靠在栏杆边，"
                    "手里的文件袋被捏出折痕。沈清的琴袋立在墙边，赵雅一路小跑，"
                    "而管家老张已经把伞递到了你的手边。\n\n"
                    "今天的误会、代考传闻和那封匿名邮件，似乎都在等你先开口。"
                ),
            }
        ],
    )


def css() -> None:
    t = THEMES[st.session_state.theme]
    bg_image = ""
    background_path = ASSET_DIR / "background.png"
    if background_path.exists():
        encoded = base64.b64encode(background_path.read_bytes()).decode("ascii")
        bg_image = (
            f"url('data:image/png;base64,{encoded}') center top / cover no-repeat fixed,"
        )
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(10,14,28,.76), rgba(10,14,28,.88)),
                {bg_image}
                {t["bg"]};
            color: {t["text"]};
        }}
        .block-container {{
            max-width: 1120px;
            padding-top: 2.2rem;
            padding-bottom: 7rem;
        }}
        h1 {{
            color: {t["text"]};
            font-size: 3rem !important;
            letter-spacing: 0 !important;
            text-shadow: 0 4px 18px rgba(0, 0, 0, .35);
        }}
        [data-testid="stChatMessage"] {{
            background: {t["panel"]};
            border: 1px solid rgba(255, 255, 255, .16);
            border-radius: 8px;
            box-shadow: 0 16px 50px rgba(0,0,0,.24);
        }}
        .stButton > button {{
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,.18);
            background: linear-gradient(180deg, {t["accent"]}, #9b7021);
            color: #121826;
            font-weight: 700;
        }}
        .stTextInput input, .stChatInput textarea {{
            border-radius: 8px;
        }}
        .status {{
            color: rgba(247,236,210,.72);
            margin-top: -.7rem;
            margin-bottom: 1rem;
        }}
        .memory-chip {{
            display: inline-block;
            margin: 0 8px 8px 0;
            padding: 6px 10px;
            border: 1px solid rgba(255,255,255,.18);
            border-radius: 999px;
            color: {t["text"]};
            background: rgba(255,255,255,.06);
            font-size: 13px;
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
    return f"""
你是中文互动剧情游戏《月影回廊》的叙事引擎。
玩家身份是“公子”，可以说话、行动、调查、安抚、试探或选择站队。

写作要求：
- 输出 180 到 260 字。
- 保持校园雨夜、豪门关系、恋爱悬疑、暗线调查的氛围。
- 每次至少让一个角色对玩家行动做出具体反应。
- 不要替玩家做最终决定。
- 结尾留下一个可继续输入的钩子。
- 可含动作描写，但不要输出系统解释。
- 当前叙事语气：{st.session_state.tone}

角色设定：
{roles}

已封存记忆：
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
            "窗外忽然掠过一束手电光，书吧玻璃上映出几个人影。",
            "远处广播短促地响了一声，又像被人突然切断。",
            "楼梯口传来脚步声，节奏很轻，却每一步都停得刚刚好。",
            "文件袋里露出半张收据，抬头正是校企奖学金项目。",
        ]
    )
    reactions = [
        f"{focus.name}听完你的话，眼神明显停了一下。她没有立刻回答，只把手里的东西抱得更紧。",
        f"{focus.name}抬头看你，像是在判断这句话里有几分真心，又有几分试探。",
        f"{focus.name}轻轻吸了口气，声音压低：公子，你现在插手，就等于告诉他们你已经知道了。",
    ]
    twist = random.choice(
        [
            "赵雅忽然把手机屏幕扣在胸口，屏幕上似乎是一张雨夜照片。",
            "管家老张往前半步，替你挡住了李经理投来的视线。",
            "沈清的琴袋拉链没有合严，里面夹着一张折起的演出名单。",
            "林雪的耳尖微红，却没有后退，像终于等到有人站到她这边。",
        ]
    )
    return (
        f"{scene}\n\n"
        f"你说：“{player_text}”\n\n"
        f"{random.choice(reactions)} {twist} 李经理笑了笑，指尖敲着文件袋："
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
        "我看向林雪，示意她先别急，把今晚看到的一切从头说。",
        "我让老张去查文件袋来源，同时请沈清留下来作证。",
        "我故意对李经理笑了笑，问他是不是还有另一份合同。",
        "我把伞递给林雪，低声告诉她，有我在。",
    ]
    add_player_message(random.choice(prompts))


def save_memory() -> None:
    recent_ai = [m["text"] for m in st.session_state.messages if m["kind"] == "ai"]
    if recent_ai:
        snippet = recent_ai[-1].split("\n")[0][:80]
        st.session_state.memory_bank.append(snippet)


def render_message(message: dict[str, str]) -> None:
    avatar = {"narrator": "🎒", "player": "🎭", "ai": "🤖"}.get(message["kind"], "💬")
    with st.chat_message(message["speaker"], avatar=avatar):
        st.markdown(message["text"])


def main() -> None:
    st.set_page_config(page_title="月影回廊", page_icon="🌙", layout="wide")
    init_state()
    css()

    st.title("月影回廊")
    engine = "DeepSeek 在线" if deepseek_key() else "离线剧情引擎"
    st.markdown(f'<div class="status">当前引擎：{engine} · 语气：{st.session_state.tone}</div>', unsafe_allow_html=True)

    for message in st.session_state.messages:
        render_message(message)

    left, mid, mem, role, theme = st.columns([1.05, 1.2, 1.35, 1.35, 1.35])
    with left:
        if st.button("🔄 重新开始", use_container_width=True):
            for key in ["messages", "memory_bank"]:
                st.session_state.pop(key, None)
            init_state()
            st.rerun()
    with mid:
        if st.button("🤖 自动推进剧情", use_container_width=True):
            auto_advance()
            st.rerun()
    with mem:
        with st.expander("💾 封存/唤醒记忆"):
            if st.button("封存最近一幕", use_container_width=True):
                save_memory()
                st.rerun()
            if st.session_state.memory_bank:
                for item in st.session_state.memory_bank[-8:]:
                    st.markdown(f'<span class="memory-chip">{item}</span>', unsafe_allow_html=True)
            else:
                st.caption("还没有封存的记忆。")
    with role:
        with st.expander("📜 角色背景"):
            for c in CHARACTERS:
                st.markdown(f"**{c.name}**：{c.role}")
    with theme:
        with st.expander("🎨 主题切换"):
            st.session_state.theme = st.radio(
                "主题",
                list(THEMES),
                index=list(THEMES).index(st.session_state.theme),
                horizontal=True,
                label_visibility="collapsed",
            )
            st.session_state.tone = st.selectbox(
                "叙事语气",
                ["暧昧试探", "悬疑推进", "温柔守护", "强势摊牌"],
                index=["暧昧试探", "悬疑推进", "温柔守护", "强势摊牌"].index(st.session_state.tone),
            )

    prompt = st.chat_input("公子，请指示...")
    if prompt:
        add_player_message(prompt)
        st.rerun()


if __name__ == "__main__":
    main()
