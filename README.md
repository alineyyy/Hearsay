# AWS Agent Hackathon — Agents for Humans

我在 [Agents for Humans Hackathon](https://agentsforhumans.devpost.com/) 上用 [AWS Strands Agents SDK](https://strandsagents.com/) 做的项目。这是我第一次做 agent 开发，仓库会随着学习和开发进度持续更新。

**当前状态：🧪 学习阶段** — 正在跑通最基础的 Strands Agent，赛道方向还没最终确定，会在正式开发前更新本 README。

## 这是什么比赛

- 用 AWS Strands Agents SDK 做一个能解决真实问题的 AI agent
- 三个赛道选一个：Everyday Agents（日常生活）/ Pro Agents（职场）/ Good Neighbor Agents（社区）
- 用 AWS AgentCore 部署可以加分（非必须）
- 截止日期：2026-09-14 17:00 PT

## 环境准备

```bash
# 1. 创建虚拟环境（推荐；如果你的机器上 venv 创建失败，直接 pip install --user 也可以）
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 AWS 凭证（Strands 默认走 Amazon Bedrock 调用 Claude）
aws configure
# 并确保在 AWS 控制台 Bedrock -> Model access 里已开通 Anthropic Claude 的模型访问权限
```

## 跑第一个 agent

```bash
python3 -u agent.py
```

`agent.py` 是照着官方 [Quickstart](https://strandsagents.com/docs/user-guide/quickstart/python/) 改的最小示例：一个 agent 挂了 3 个工具（`calculator`、`current_time`、自定义的 `letter_counter`），丢一句自然语言指令给它，它自己决定调用哪些工具、调几次、最后怎么组织回答。

## Strands Agents 是什么（自己整理的笔记）

- **Agent = LLM + 工具（tools）+ 一个"思考 → 调用工具 → 再思考 → 回答"的循环。** SDK 本身没有额外的服务端/调度器，`Agent(...)` 就是你进程里的一个普通 Python 对象。
- **模型可插拔**：默认用 Amazon Bedrock 上的 Claude，也可以换成 Anthropic/OpenAI/Google/Ollama 等，通常只是换一行代码 + 装对应的包。
- **工具（tool）**：一个普通函数，用 `@tool` 装饰器标记一下，函数签名和 docstring 会被自动转成"这个工具是干嘛的"说明喂给模型。也可以通过 MCP（Model Context Protocol）接入外部工具/服务。
- **多 agent 编排**：可以把多个 agent 组合起来（比如一个负责抽取信息、一个负责决策/写作），适合拆分复杂任务。
- **AgentCore**：AWS 提供的托管部署层（Runtime / Gateway / Memory / Identity / Observability），本地写好的 Strands agent 可以部署上去跑在云端，这是比赛里的加分项。

## 学习 & 开发路线（给自己看的 checklist）

- [x] 注册 AWS 账号 + AWS Builder ID
- [x] 装好 strands-agents，跑通第一个 hello world agent
- [ ] 申请 $50 AWS credits，确认 Bedrock 里 Claude 的模型访问权限已开通
- [ ] 过一遍官方 [Examples](https://strandsagents.com/docs/examples/)，理解自定义工具、多 agent 编排、MCP 集成
- [ ] 确定赛道方向 + 具体项目想法
- [ ] 写出第一版能跑的 agent（覆盖真实的一个使用场景）
- [ ] 补齐架构图、完整 README
- [ ] （加分项）用 AgentCore 部署
- [ ] 录 5 分钟以内的 demo + pitch 视频，发 YouTube/Vimeo
- [ ] 提交到 Devpost

## 参考资料

- Strands Agents Quickstart: https://strandsagents.com/docs/user-guide/quickstart/overview/
- Strands Agents Examples: https://strandsagents.com/docs/examples/
- Amazon Bedrock AgentCore 文档: https://docs.aws.amazon.com/bedrock-agentcore/
- Strands 部署到 AgentCore Runtime: https://aws.github.io/bedrock-agentcore-starter-toolkit/user-guide/runtime/quickstart.html
- 比赛主页: https://agentsforhumans.devpost.com/
- 比赛 Resources 页: https://agentsforhumans.devpost.com/resources

## License

MIT — 见 [LICENSE](./LICENSE)
