# 重生之我该如何选择

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

然后编辑 `.streamlit/secrets.toml` 填入 `DEEPSEEK_API_KEY`。部署到 Streamlit Cloud 后，其他玩家打开网页时会使用你的服务端 API key 调用 DeepSeek，但他们看不到 key。

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

代码查看和修改位置：

- GitHub 仓库：`https://github.com/wai871077-Liu/ai-story-game`
- 本地目录：`/Users/shuangshuang/Desktop/game/ai_story_game`
- 主要代码：`app.py`

修改后同步部署：

```bash
git add .
git commit -m "Update story game"
git push
```

Streamlit Cloud 会从 GitHub 自动更新。如果没有自动更新，可以在 Streamlit Cloud app 页面手动点击 Reboot 或 Rerun。

普通玩家访问游戏页面时不会看到 GitHub 仓库链接。GitHub 是否公开只影响别人能不能从 GitHub 搜到代码；如果想隐藏源码，需要把仓库改为 Private，并确认 Streamlit Cloud 仍有访问权限。

## 玩法

- 在底部输入“柳书昂”的行动或台词。
- 点击发送，系统推进一段剧情。
- 外观支持深色和浅色。
- 括号内是心理、动作和环境提示；括号外是角色真正说出口的对白。
- 可以存储记忆文件，下次上传后继续上一次剧情。
- 剧情可能随机触发紧急事件，主要角色不会死亡，但选择会带来关系和线索后果。
