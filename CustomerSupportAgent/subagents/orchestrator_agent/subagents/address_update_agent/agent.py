from google.adk.agents import LlmAgent

from CustomerSupportAgent.prompt import *
from CustomerSupportAgent.tools import *
from CustomerSupportAgent.config import *

address_update_agent = LlmAgent(
    model=MODEL_NAME,
    name="address_update_agent",
    description="Updates the billing address for the user",
    instruction=prompt_update_address_task,
    tools=[update_address],
)