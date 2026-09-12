"""
Hello World: my first Strands agent.

Kept from the first day of the project as a record of where this started. It is not part
of Hearsay — the product lives in src/.

The smallest useful mental model of an agent:
    a model + a set of tools + a loop that decides which tool to reach for.

Before running:
  1. pip install strands-agents strands-agents-tools
  2. AWS credentials configured for Amazon Bedrock (aws configure, or env vars)
  3. Model access granted for Anthropic Claude in the Bedrock console

Run:
  python3 -u agent.py
"""

from strands import Agent, tool
from strands_tools import calculator, current_time


# The @tool decorator turns an ordinary function into something the model can call.
# The type hints and the docstring become the tool's specification — which is why both
# matter far more than they look: they are the instructions the model reads.
@tool
def letter_counter(word: str, letter: str) -> int:
    """Count how many times a letter appears in a word."""
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0
    if len(letter) != 1:
        raise ValueError("letter must be a single character")
    return word.lower().count(letter.lower())


# Two built-in tools and one of my own. Nothing here says when to use which — the agent
# works that out from the question, which is the part that felt like magic at first.
agent = Agent(tools=[calculator, current_time, letter_counter])

message = """
I have four requests:
1. What time is it right now?
2. Calculate 3111696 / 74088
3. How many letter R's are in the word "strawberry"?
4. In one sentence, how did you decide which tools to call?
"""

if __name__ == "__main__":
    agent(message)
