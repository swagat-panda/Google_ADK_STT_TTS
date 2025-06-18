import os
import json


APP_NAME = "banking_bot_app"
USER_ID = "test_user_42"
SESSION_ID = "session_tool_agent_xyz"
# SESSION_ID_SCHEMA_AGENT = "session_schema_agent_xyz"
MODEL_NAME = "gemini-2.0-flash"

user_data = {
    "user_authenticated": 0,
    "user_name": "John Smith",
    "user_debit_card_digits": "1890",
    "user_account_balance": 10000,
    "user_credit_card_bill":1500,
    "user_credit_card_bill_min_pay":100,
    "user_house_number":42,
    "user_street_name":"Oak St",
    "user_zip_code":"89530"
}