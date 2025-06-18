from google.adk.agents import LlmAgent

from CustomerSupportAgent.prompt import *
from CustomerSupportAgent.tools import *
from CustomerSupportAgent.config import *

bill_payment_agent = LlmAgent(
    model=MODEL_NAME,
    name="bill_payment_agent",
    description="Pays the credit card bill for the user",
    instruction=prompt_make_payment_task,
    tools=[pay_credit_card_bill]
)