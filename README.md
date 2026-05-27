# 月影回廊

一个类似 `oliversgame.streamlit.app` 的中文互动剧情游戏。界面使用 Streamlit，剧情生成优先调用 DeepSeek API；没有 API Key 时会自动使用内置离线剧情引擎，方便先试玩和改规则。

## 运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 配置 DeepSeek

方式一，使用环境变量：

```bash
export DEEPSEEK_API_KEY="你的 key"
export DEEPSEEK_MODEL="deepseek-chat"
streamlit run app.py
```

方式二，使用 Streamlit secrets：

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

然后编辑 `.streamlit/secrets.toml` 填入 `DEEPSEEK_API_KEY`。

## 部署到 Streamlit Community Cloud

1. 把本目录上传到 GitHub 仓库。
2. 打开 `https://share.streamlit.io/`，连接 GitHub。
3. 创建 app，选择仓库、分支和入口文件 `app.py`。
4. 在 Advanced settings 的 Secrets 中填写：

```toml
DEEPSEEK_API_KEY = "你的 key"
DEEPSEEK_MODEL = "deepseek-chat"
```

5. 点击 Deploy，部署完成后会得到一个 `*.streamlit.app` 链接。

不要把 `.streamlit/secrets.toml` 上传到 GitHub。仓库里只保留 `.streamlit/secrets.toml.example`。

## 部署后修改

可以继续修改代码。每次把修改提交并推送到 GitHub 后，Streamlit Cloud 会自动重新部署。DeepSeek key 不需要重新写进代码，只在 Streamlit 的 Secrets 页面维护。

## 玩法

- 在底部输入“公子”的行动或台词。
- 点击发送，系统推进一段剧情。
- 可以自动推进剧情、保存/唤醒记忆、查看角色背景、切换主题。
- 选择不同语气会影响 AI 生成方向。
