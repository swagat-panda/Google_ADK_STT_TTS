from google.adk.agents import Agent
from verification.prompt import PROMPT
from verification.tools.verify_user import verifyUserDetails

root_agent = Agent(
    model="gemini-2.0-flash",
    name='verification',
    description="You are an AI assistant tasked with verifying user identity. Your goal is to collect the user's full name and date of birth, and then use a specific tool to perform the verification.",
    instruction=PROMPT,
    output_key="verification",
    tools=[verifyUserDetails]
)
