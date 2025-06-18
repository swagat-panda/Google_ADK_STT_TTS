from google.adk.agents import LlmAgent

from CustomerSupportAgent.prompt import *
from CustomerSupportAgent.tools import *
from CustomerSupportAgent.config import *

authentication_agent = LlmAgent(
    model=MODEL_NAME,
    name="authentication_agent",
    description="Authenticates a user",
    instruction=prompt_auth_task,
    tools=[authenticate_user],
)