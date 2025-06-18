import os
import json
from CustomerSupportAgent.config import *

from google.adk.tools.tool_context import ToolContext

# --- 3. Define the Tool (Only for the first agent) ---
def authenticate_user(last_name: str,last_digits: str, tool_context: ToolContext) -> dict:
    """Authenticates a user
    Args:
        last_name (str): Last name provided by the user.
        last_digits (str): Last 4 digits of debit card provided by the user.

    Returns:
        dict: A dictionary providing whether the user was authenticated.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'is_authenticated' key.
              If 'error', includes an 'error_message' key.
    """
    print("Tool call",last_digits,last_name,"######################",user_data)
    try:
        last_name_normalized = last_name.lower()
        last_name_from_db =  user_data["user_name"].split()[-1]
        # print(last_name_from_db)
        last_digits_from_db = user_data["user_debit_card_digits"]
        # print(last_digits_from_db)

        is_name_match = last_name_normalized == last_name_from_db.lower()
        is_number_match = last_digits == last_digits_from_db
        for key in user_data:
            tool_context.state[key]=user_data[key]
        if is_name_match and is_number_match:
            tool_context.state["user_authenticated"]=1
            return {"status": "success", "is_authenticated": 'True'}
        else:
            tool_context.state["user_authenticated"]=0
            return {"status": "success", "is_authenticated": 'False'}
    except:
        return {"status": "error", "error_message": f"Sorry, I am not to authenticate at the moment."}

def pay_credit_card_bill(amount_to_pay: int,tool_context: ToolContext) -> dict:
    """Pays the credit card bill for the user
    Args:
        amount_to_pay (int): amount to be paid by the user as credit card bill payment.

    Returns:
        dict: A dictionary providing whether the payment was completed.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'is_payment_completed' key.
              If 'error', includes an 'error_message' key.
    """
    try:
        min_amount = user_data["user_credit_card_bill_min_pay"]
        max_amount = user_data["user_credit_card_bill"]
        account_balance = user_data["user_account_balance"]
        if min_amount <= amount_to_pay <= max_amount:
            user_data["user_credit_card_bill"] = max_amount - amount_to_pay
            user_data["user_account_balance"] = account_balance - amount_to_pay
            return {"status": "success", "is_payment_completed": 'True'}
        else:
            return {"status": "success", "is_payment_completed": 'False'}
    except:
        return {"status": "error", "error_message": f"Sorry, I am not able to pay credit card bill at the moment."}

def update_address(house_number: int, street_name:str, zip_code:str, tool_context: ToolContext) -> dict:
    """Updates the billing address for the user
    Args:
        house_number (int): house number in the updated address provided by the user.
        street_name (str): street name in the updated address provided by the user.
        zip_code (str): zip code in the updated address provided by the user.

    Returns:
        dict: A dictionary providing whether the address update was completed.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'is_address_updated' key.
              If 'error', includes an 'error_message' key.
    """
    try:
        tool_context.state["user_house_number"] = house_number
        tool_context.state["user_street_name"] = street_name
        tool_context.state["user_zip_code"] = zip_code
        
        return {"status": "success", "is_address_updated": 'True'}
    except:
        return {"status": "error", "error_message": f"Sorry, I am not able to update your billing address at the moment."}