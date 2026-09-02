"""
Hello World: 我的第一个 Strands Agent

这是根据官方 Quickstart 改的最小示例，用来理解 Strands Agents 的核心概念：
  Agent = 大语言模型(LLM) + 一组工具(tools) + 一个"思考-调用工具-回答"的循环

运行前提：
  1. 已 `pip install strands-agents strands-agents-tools`
  2. 本机已配置好可以调用 Amazon Bedrock 的 AWS 凭证
     (跑 `aws configure`，或设置 AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY 环境变量)
  3. 你的 AWS 账号已经在 Bedrock 控制台里对 Claude 系列模型开启了访问权限
     (Bedrock 控制台 -> Model access -> 申请 Anthropic Claude 的访问)

运行方式：
  python3 -u agent.py
"""

from strands import Agent, tool
from strands_tools import calculator, current_time


# 自定义一个工具：用 @tool 装饰器把一个普通 Python 函数变成 agent 可以调用的工具。
# 函数的类型注解和 docstring 会被自动转成告诉 LLM "这个工具是干嘛的、参数是什么"的说明。
@tool
def letter_counter(word: str, letter: str) -> int:
    """统计某个单词里某个字母出现了几次。"""
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0
    if len(letter) != 1:
        raise ValueError("letter 参数必须是单个字符")
    return word.lower().count(letter.lower())


# 创建 agent：把内置工具(calculator, current_time)和自定义工具(letter_counter)一起交给它。
# 默认模型走 Amazon Bedrock 上的 Claude；不用你手写"什么时候该用哪个工具"的逻辑，
# agent 会自己根据用户的话去判断该调用哪个工具、调用几次、以及最后怎么组织回答。
agent = Agent(tools=[calculator, current_time, letter_counter])

message = """
我有4个请求：
1. 现在几点？
2. 计算 3111696 / 74088
3. 单词 "strawberry" 里有几个字母 r？
4. 用一句话说说你（这个 agent）刚才是怎么决定调用哪些工具的
"""

if __name__ == "__main__":
    agent(message)
