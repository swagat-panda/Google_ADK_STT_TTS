from google.adk.agents import LlmAgent

from CustomerSupportAgent.prompt import *
from CustomerSupportAgent.tools import *
from CustomerSupportAgent.config import *
from .subagents.account_info_agent.agent import account_info_agent
from .subagents.bill_payment_agent.agent import bill_payment_agent
from .subagents.address_update_agent.agent import address_update_agent

orchestrator_agent = LlmAgent(
    model=MODEL_NAME,
    name="orchestrator_agent",
    description="Primary agent that talks to the user and orchestrates tasks",
    instruction=prompt_system_task,
    sub_agents=[account_info_agent,bill_payment_agent,address_update_agent],
)