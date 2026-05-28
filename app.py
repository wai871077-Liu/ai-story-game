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
        "女主，已经成年的大学生兼项目实习生。她清冷坚韧，把委屈藏在礼貌后面，最难相信别人，也最容易被真诚打动。",
        "她收到过一封匿名提醒，知道罗经理正在借一份文件制造污名。",
        "克制、敏感、偶尔露出柔软。",
    ),
    Character(
        "柳书昂",
        "玩家扮演的成年主人公。重生后，他必须重新选择如何保护小雨，并赢得她的爱。",
        "他记得前世错过小雨的结局，因此这一次不想再沉默。",
        "由玩家输入决定，不替玩家做决定。",
    ),
    Character(
        "徐佳珍",
        "小雨身边的成年同学，非常嫉妒小雨的才华，同时暗恋柳书昂。",
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
        "反派角色，校企合作赞助方代表。笑容体面，手段并不体面。",
        "他正用伪造的把柄逼小雨签一份虚假证明，同时试图拿柳书昂当筹码。",
        "圆滑、压迫、总留退路。",
    ),
    Character(
        "沈知衡",
        "小雨的大学导师兼项目负责人，温和克制但掌控欲强。",
        "他掌握罗经理资金链问题的一部分证据，却不愿轻易交给柳书昂。",
        "冷静、克制、会用温柔制造压力。",
    ),
    Character(
        "许曼宁",
        "小雨最好的闺蜜，嘴上强势，实际非常护短。",
        "她知道小雨曾偷偷保存过一份关键备份，会替小雨试探柳书昂是否真心。",
        "直白、护短、锋利，必要时会逼问玩家。",
    ),
    Character(
        "林昭",
        "罗经理身边的年轻法务，冷静理性，承担暗恋与策反线。",
        "他发现罗经理合同里有致命漏洞，也知道自己继续沉默会伤害小雨。",
        "理性、压抑、克制，偶尔流露偏袒。",
    ),
    Character(
        "唐晚",
        "小雨的竞争对手，欣赏小雨却不愿承认。",
        "她手里有一段能证明小雨清白的会议录音，但公开时机取决于局势。",
        "骄傲、尖锐、好胜，会制造误会和竞争压力。",
    ),
]

PLACES = [
    "大学图书馆闭馆前十分钟，窗外的雨把路灯晕成一圈柔软的光。",
    "联合实验室侧门，雨后的桂花香混着小雨外套上淡淡的洗衣液味。",
    "校企合作项目会议室外，玻璃墙上映出罗经理的笑。",
    "创业中心天台，晚风吹乱合同边角，城市灯光在远处缓慢亮起。",
    "医务室门口，消毒水味道很淡，小雨的袖口还沾着一点咖啡渍。",
    "大学城便利店檐下，雨珠从遮阳棚边缘一颗颗坠下。",
    "空无一人的阶梯报告厅，投影幕布上还停着项目名单的残影。",
    "末班地铁入口，徐佳珍把手机屏幕攥得发烫。",
    "旧社团活动室，柜门没有关严，里面露出一角被折过的合同。",
    "创业园地下车库，罗经理的车停在监控死角。",
    "项目办公室，碎纸机旁落着半截没有粉碎干净的签名页。",
    "学院后门，声控灯忽明忽暗，小雨抱着资料站在阴影边缘。",
    "档案室门外，钥匙还插在锁孔里，门缝里透出一线冷白灯光。",
    "律所会客室，林昭把一杯冷掉的咖啡推到桌边，却迟迟没有开口。",
    "导师办公室外，沈知衡的门虚掩着，里面传来罗经理压低的声音。",
]

OPENING_SCENE_DETAILS = [
    (
        "重生后的第一天，柳书昂终于回到那个决定命运的岔路口。小雨抱着项目资料从转角出现，"
        "罗经理靠在栏杆边，手里的文件袋被捏出折痕。徐佳珍站在不远处盯着小雨，"
        "眼神里藏着嫉妒和不甘，而管家老张已经把伞递到了柳书昂手边。"
    ),
    (
        "项目入选名单刚发出来，小雨的名字在第一行，旁边却多了一封匿名举报邮件。"
        "徐佳珍看着名单咬紧嘴唇，罗经理站在人群外，像早就等着这一幕发生。"
        "柳书昂记得前世，小雨就是从这一天开始被流言推远。"
    ),
    (
        "雨声盖住了走廊尽头的争执。小雨低头整理湿掉的资料，罗经理把一份证明推到她面前，"
        "语气温和得近乎残忍。徐佳珍躲在拐角，手机镜头亮了一瞬，又立刻暗下去。"
    ),
    (
        "报告厅已经清场，只剩小雨桌上的电脑还亮着。她在项目材料上写到一半，"
        "却被罗经理递来的文件打断。柳书昂站在门口，清楚地记得前世自己就是在这里沉默了。"
    ),
    (
        "校企赞助会马上开始，罗经理带着笑意走进后台，小雨被临时叫去核对名单。"
        "徐佳珍看见柳书昂跟过去，指尖几乎掐进掌心。空气里全是将要失控的预感。"
    ),
    (
        "档案室的灯突然亮起，小雨手里握着一张旧收据，脸色比纸还白。"
        "管家老张站在门外低声提醒，罗经理的人已经到了楼下。柳书昂知道，这次不能再慢一步。"
    ),
]

LETHAL_INTENT_WORDS = ["杀", "杀死", "弄死", "刺死", "捅死", "打死", "毒死", "勒死", "枪杀", "致命"]

EMERGENCY_EVENTS = [
    "证据类：关键录音突然损坏，只剩一段模糊的背景音能证明有人撒谎。",
    "证据类：小雨保存的截图被远程删除，但许曼宁记得截图里出现过一个时间戳。",
    "证据类：匿名包裹送到项目办公室，里面是一份被调包过的合同。",
    "证据类：文件袋被人从桌边抢走，逃走的人影拐进监控死角。",
    "情感类：小雨误会柳书昂提前和罗经理交易，第一次主动后退半步。",
    "情感类：徐佳珍情绪失控，当众承认自己嫉妒小雨，也不甘心柳书昂只看见小雨。",
    "情感类：许曼宁挡在小雨身前，逼问柳书昂到底是保护小雨，还是享受被依赖。",
    "情感类：林昭突然替小雨说话，语气冷静，却让罗经理察觉他已经动摇。",
    "情感类：唐晚故意刺激小雨，说她总是假装不在乎，其实最怕柳书昂转身离开。",
    "反派类：罗经理突然带着假证人出现，要求小雨当场签字澄清。",
    "反派类：赞助方临时施压，威胁撤掉小雨所在项目的全部资源。",
    "反派类：偷拍视频被发到群里，标题故意误导所有人。",
    "时间类：会议还有三分钟开始，柳书昂必须先决定保住证据还是先追小雨。",
    "时间类：门禁即将关闭，档案室和停车场只能选一个方向。",
    "记忆类：前世失败片段突然闪回，柳书昂想起自己曾在同一个地方说错一句话。",
    "记忆类：小雨的一句低声质问触发既视感，柳书昂意识到结局正在重复。",
    "新角色类：沈知衡突然介入，要求柳书昂不要把小雨拖进更危险的局。",
    "新角色类：林昭把一张名片压在杯底，暗示罗经理的合同有漏洞。",
    "新角色类：唐晚抢先公开一半信息，让小雨陷入更难解释的局面。",
    "新角色类：陌生记者追问小雨是否承认造假，镜头已经对准她的脸。",
    "环境类：整层楼突然停电，安全门自动落锁，走廊只剩应急灯。",
    "环境类：暴雨封住校门，罗经理的人却已经进了地下车库。",
    "环境类：电梯停在半层，电话信号断断续续，只传来一声压低的求救。",
]

VIOLENCE_INTERRUPTION_EVENTS = [
    "暴力化解类：柳书昂试图做出致命举动前，刺耳警报突然响起，目标被人拽离原地，局势转向更危险的对峙。",
    "暴力化解类：动作失控的一瞬间，前世记忆猛烈闪回，柳书昂的手偏开，只造成非致命后果，却留下无法回避的关系裂痕。",
    "暴力化解类：第三方突然冲入现场挡开攻击，证据随混乱被转移，所有人都意识到柳书昂已经被逼到边缘。",
    "暴力化解类：监控灯骤然亮起，目标趁混乱逃脱，罗经理反而抓住机会把局面包装成对柳书昂不利的证据。",
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
    st.session_state.setdefault("pending_player_text", "")
    st.session_state.setdefault("pending_emergency_event", "")
    st.session_state.setdefault("pending_memory_notice", "")
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
    detail = random.choice(OPENING_SCENE_DETAILS)
    return (
        f"场景记录：{place}\n\n"
        f"{detail}\n\n"
        "这一次，柳书昂的目标很明确：保护小雨，靠近小雨，查清罗经理的局，最终让她愿意把手交给自己。"
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
            max-width: 1280px;
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
            padding: 22px 28px;
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
        .guide-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(24px) saturate(150%);
            width: 260px;
            margin: 0;
            position: fixed;
            right: max(18px, calc((100vw - 1280px) / 2 + 18px));
            bottom: 92px;
            z-index: 20;
        }}
        .guide-title {{
            color: var(--text);
            font-weight: 800;
            margin-bottom: 12px;
        }}
        .guide-list {{
            margin: 0;
            padding-left: 18px;
            color: var(--muted);
            font-size: .88rem;
            line-height: 1.55;
        }}
        .guide-list li {{
            margin-bottom: 8px;
        }}
        .guide-emphasis {{
            color: var(--text);
            font-weight: 800;
        }}
        .hint-note {{
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
            .guide-card {{
                position: static;
                width: auto;
                margin: 8px 0 18px;
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
    emergency = st.session_state.get("pending_emergency_event", "")
    emergency_line = f"本轮紧急事件：{emergency}" if emergency else "本轮没有强制紧急事件，但仍要保持张力。"
    return f"""
你是中文互动剧情游戏《{APP_TITLE}》的叙事引擎。
所有主要角色均为成年人。背景是大学/职场交织的恋爱悬疑故事。
玩家身份是“柳书昂”，重生后重新面对关键选择。
玩家目标：获得女主“小雨”的爱，保护她，查清罗经理的局，并最终和小雨在一起。

写作要求：
- 输出 180 到 260 字。
- 整体氛围：成年恋爱、重生选择、情感拉扯、职场/大学项目暗线调查。
- 重点描写小雨对柳书昂行动的反应；罗经理是反派，徐佳珍嫉妒小雨且暗恋柳书昂。
- 不要替玩家做最终决定。
- 结尾留下一个可继续输入的钩子。
- 严格使用恋爱游戏对话格式：括号里面写心理活动、动作、环境提示；括号外写角色真正说出口的话。
- 示例：小雨：（她攥紧书角，眼神躲开了一瞬）柳书昂，你为什么突然帮我？
- 不要输出系统解释，不要用项目符号。
- 允许成熟暧昧、亲密氛围、吻戏、占有欲、吃醋、拉扯和情感张力，但不要出现生殖器官名称，不要写露骨器官描写。
- 玩家指令不能太离谱：如果玩家输入瞬间解决全部问题、破坏设定、摧毁系统、夺取叙事权或超出现实能力的行为，要自然转化成条件不足、被打断、角色不配合、证据不够或引发新危机。
- 柳书昂、小雨、徐佳珍、管家老张、罗经理无法死亡；所有拥有名字的角色都很难死亡。不要直接告诉玩家“角色无法死亡”，要用剧情自然化解致命结果。
- 游戏系统、叙事引擎、存档机制、玩家身份不能被摧毁、删除、夺取或绕过。
- 可以自然加入新的成年命名角色，但不能抢走小雨主线。
- {emergency_line}
- 如果本轮有紧急事件，事件必须改变当前局势，不能只当旁白装饰。

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


def has_lethal_intent(text: str) -> bool:
    return any(word in text for word in LETHAL_INTENT_WORDS)


def maybe_emergency_event(player_text: str) -> str:
    if has_lethal_intent(player_text):
        return random.choice(VIOLENCE_INTERRUPTION_EVENTS)
    if random.random() < 0.25:
        return random.choice(EMERGENCY_EVENTS)
    return ""


def offline_generate(player_text: str) -> str:
    emergency = st.session_state.get("pending_emergency_event", "")
    scene = random.choice(
        [
            "远处忽然掠过一束车灯，玻璃上映出几个人影。",
            "会议室广播短促地响了一声，又像被人突然切断。",
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
    event_text = f"\n\n紧急事件：（{emergency}）" if emergency else ""
    return (
        f"{scene}\n\n"
        f"柳书昂：（你向前一步，声音压得很稳）{player_text}\n\n"
        f"{event_text}"
        "小雨：（她抱紧书本，睫毛轻轻颤了一下，像是不敢立刻相信你）"
        "柳书昂，你为什么……突然站在我这边？\n\n"
        f"{twist}\n\n"
        "小雨：（她终于抬头看你，眼底的防备松动了一点）如果你真的知道些什么，就别只说一半。"
    )


def queue_player_message(text: str) -> None:
    st.session_state.messages.append({"speaker": "柳书昂", "kind": "player", "text": text})
    st.session_state.pending_player_text = text
    st.session_state.pending_emergency_event = maybe_emergency_event(text)


def complete_pending_response() -> None:
    text = st.session_state.get("pending_player_text", "")
    if not text:
        return
    try:
        answer, mode = deepseek_generate(text)
    except Exception as exc:
        answer = offline_generate(text) + f"\n\n（DeepSeek 调用失败，已切换离线剧情：{exc}）"
        mode = "offline"
    st.session_state.messages.append(
        {"speaker": "剧情引擎" if mode == "deepseek" else "离线引擎", "kind": "ai", "text": answer}
    )
    st.session_state.pending_player_text = ""
    st.session_state.pending_emergency_event = ""


def auto_advance() -> None:
    prompts = [
        "我看向小雨，示意她先别急，把今晚看到的一切从头说。",
        "我让老张去查文件袋来源，同时请小雨先相信我一次。",
        "我故意对罗经理笑了笑，问他是不是还有另一份合同。",
        "我把伞递给小雨，低声告诉她，这一次我会先选她。",
    ]
    queue_player_message(random.choice(prompts))


def reset_story() -> None:
    for key in ["messages", "memory_bank", "active_memory", "pending_player_text", "pending_emergency_event"]:
        st.session_state.pop(key, None)
    init_state()


def refresh_opening_scene() -> None:
    for key in ["messages", "active_memory", "pending_player_text", "pending_emergency_event"]:
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

    st.session_state.messages = messages
    st.session_state.memory_bank = [
        str(item) for item in data.get("memory_bank", []) if isinstance(item, str)
    ][-12:]
    st.session_state.active_memory = str(data.get("active_memory", ""))
    if data.get("appearance") in APPEARANCES:
        st.session_state.pending_restore_appearance = data["appearance"]
    st.session_state.pending_player_text = ""
    st.session_state.pending_emergency_event = ""

    last_ai = next((m["text"] for m in reversed(messages) if m["kind"] == "ai"), "")
    if last_ai and not st.session_state.active_memory:
        st.session_state.active_memory = last_ai.split("\n")[0][:120]
    return True, "已唤醒这份记忆，可以继续上一次的回忆来游戏。"


def apply_pending_restore() -> None:
    appearance = st.session_state.pop("pending_restore_appearance", "")
    if appearance in APPEARANCES:
        st.session_state.appearance = appearance


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
                <div class="character-role">秘密：{character.secret}</div>
                <div class="character-role">表现：{character.style}</div>
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
    if st.button("刷新开场剧情", use_container_width=True):
        refresh_opening_scene()
        st.rerun()
    st.markdown(
        '<div class="hint-note">刷新页面后会删除记录，请及时存储记忆</div>',
        unsafe_allow_html=True,
    )


def render_character_panel() -> None:
    with st.expander("人物介绍", expanded=False):
        render_character_cards()


def render_game_guide() -> None:
    st.markdown(
        """
        <div class="guide-card">
            <div class="guide-title">游戏指南</div>
            <ul class="guide-list">
                <li>自由输入柳书昂的行动或对白。</li>
                <li><span class="guide-emphasis">括号（）内</span>是心理活动、动作、表情和环境提示。</li>
                <li><span class="guide-emphasis">括号外</span>均是角色真正说出口的对话。</li>
                <li>存储记忆后，下次可上传继续。</li>
                <li>刷新开场会清空当前记录。</li>
                <li>剧情可能随机触发紧急事件。</li>
                <li>玩家指令不能太离谱，过强行动会转成剧情后果。</li>
                <li>主要角色不会死亡，但剧情不会直接说明规则。</li>
            </ul>
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
                    st.session_state.pending_memory_notice = message
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
        queue_player_message(text.strip())
        st.rerun()


def scroll_to_bottom() -> None:
    st.html(
        """
        <script>
        const scrollToBottom = () => {
            try {
                const doc = window.parent.document;
                const anchor = doc.getElementById("latest-message-anchor");
                if (anchor) {
                    anchor.scrollIntoView({ behavior: "smooth", block: "end" });
                    return;
                }
                const scroller = doc.scrollingElement || doc.documentElement || doc.body;
                scroller.scrollTo({ top: scroller.scrollHeight, behavior: "smooth" });
            } catch (error) {
                window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
            }
        };
        setTimeout(scrollToBottom, 60);
        setTimeout(scrollToBottom, 300);
        setTimeout(scrollToBottom, 900);
        setTimeout(scrollToBottom, 1500);
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="✦", layout="wide")
    init_state()
    apply_pending_restore()
    css()

    st.title(APP_TITLE)

    story_col, guide_col = st.columns([5, 1], gap="large")
    with story_col:
        render_control_panel()
        render_memory_panel()
        if st.session_state.pending_memory_notice:
            st.success(st.session_state.pending_memory_notice)
            st.session_state.pending_memory_notice = ""
        render_character_panel()

        for message in st.session_state.messages:
            render_message(message)
        st.markdown('<div id="latest-message-anchor"></div>', unsafe_allow_html=True)

        render_player_input()
        if st.session_state.pending_player_text:
            with st.spinner("小雨正在回应..."):
                complete_pending_response()
            st.rerun()
    with guide_col:
        render_game_guide()
    scroll_to_bottom()


if __name__ == "__main__":
    main()
