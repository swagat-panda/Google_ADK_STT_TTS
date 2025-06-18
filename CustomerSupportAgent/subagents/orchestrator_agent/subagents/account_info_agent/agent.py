from google.adk.agents import LlmAgent

from CustomerSupportAgent.prompt import *
from CustomerSupportAgent.tools import *
from CustomerSupportAgent.config import *

account_info_agent = LlmAgent(
    model=MODEL_NAME,
    name="account_info_agent",
    description="Provides information about account and credit card bill and billing address",
    instruction=prompt_account_info_task
)