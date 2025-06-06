from google.adk.tools import ToolContext, FunctionTool

def verifyUserDetails(fullName :str,dateOfBirth:str,tool_context: ToolContext):
    '''
    Verifies a user's identity by checking their provided full name and date of birth against a secure database. Returns a verification status and, if successful, user ID or relevant details.
    Args:
        fullName:
        dateOfBirth:
        tool_context:

    Returns:
    {Status:Boolean,user_id:str}
    '''

    print(fullName,dateOfBirth,type(tool_context))
    tool_context.state["verification_status"] = True

    return {"Status":True,"user_id":"abc1234"}


