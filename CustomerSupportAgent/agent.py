from typing import AsyncGenerator
from typing_extensions import override
from google.adk.agents import LlmAgent,BaseAgent,SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from CustomerSupportAgent.prompt import *
from CustomerSupportAgent.tools import *
from CustomerSupportAgent.config import *

from CustomerSupportAgent.subagents.authentication_agent.agent import authentication_agent
from CustomerSupportAgent.subagents.orchestrator_agent.agent import orchestrator_agent

import os

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "testvertexbot-1a0b45623d70.json"

class CustomerSupportAgent(BaseAgent):
    """
    Custom Agent for customer support for user in banking domain.
    """
    # --- Field Declarations for Pydantic ---
    # Declare the agents passed during initialization as class attributes with type hints
    orchestrator: LlmAgent
    authenticator: LlmAgent

    authentication_pipeline: SequentialAgent

    def __init__(self,
                name: str,
                orchestrator: LlmAgent,
                authenticator: LlmAgent,
                ):
        """
        Initializes the CustomerSupportAgent.

        Args:
            name: The name of the agent.
            orchestrator: An LlmAgent to talk to the user and perform tasks.
            authenticator: An LlmAgent to autheticate the user.
        """
        authentication_pipeline = SequentialAgent(name="Authentication_pipeline",sub_agents=[orchestrator,authenticator])

        super().__init__(name=name,
                        orchestrator=orchestrator,
                        authenticator=authenticator,
                        authentication_pipeline=authentication_pipeline)

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Implements the custom logic for the customer support.
        Uses the instance attributes assigned by Pydantic (e.g., self.authentication_pipeline).
        """
        is_authentication_completed = ctx.session.state.get("user_authenticated")
        print(is_authentication_completed,"#################")
        if is_authentication_completed is None:
            is_authentication_completed=0
        if is_authentication_completed == 0:
            async for event in self.authentication_pipeline.run_async(ctx):
                yield event
        else:
            async for event in self.orchestrator.run_async(ctx):
                yield event
                
root_agent = CustomerSupportAgent(
                name="CustomerSupportAgent",
                # model="gemini-2.0-flash",
                orchestrator=orchestrator_agent,
                authenticator=authentication_agent,
                )