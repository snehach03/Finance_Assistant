import os
import time
import json
import requests
from dotenv import load_dotenv
from app.utils.json_helpers import clean_json_response

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"


def call_gemini_with_retry(payload, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            return response

        if response.status_code == 429:
            wait_time = (attempt + 1) * 5
            print(f"Rate limited. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            continue

        return response

    return response


def categorize_transactions_batch(transactions):
    transaction_text = "\n".join(transactions)
    prompt = f"""
You are a financial transaction classifier.

Classify each bank transaction into EXACTLY ONE of the following categories:

Food
Transport
Shopping
Entertainment
Bills
Rent
Income
Refund
Recharge
Travel
Other

Transactions:

{transaction_text}

Instructions:
- Return ONLY a valid JSON object.
- The key should be the transaction description.
- The value should be exactly one category from the list above.
- Do not include explanations.
- Do not use markdown.
"""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = call_gemini_with_retry(payload, max_retries=3)

    if response.status_code != 200:
        return None

    result = response.json()
    ans = result["candidates"][0]["content"]["parts"][0]["text"]
    ans = clean_json_response(ans)
    mapping = json.loads(ans)
    return mapping


def generate_ai_summary(analytics):
    summary = f"""
Financial Statistics

Total Income: ₹{analytics['total_credit']}
Total Expense: ₹{analytics['total_debit']}
Net Balance: ₹{analytics['net_balance']}
Savings Rate: {analytics['Savings_Rate']:.2f}%
Monthly Savings: {analytics['Monthly_Saving_Analysis']}
Average Debit Transaction: ₹{analytics['Average_Debit_Transaction_Amount']:.2f}
Monthly Spending: {analytics['Monthly_Spending_Analysis']}
Monthly Income: {analytics['income']}
Top Expense Transactions: {analytics['Top_5_Highest_Expense_Transactions']}
Lowest Expense Transactions: {analytics['Top_3_Lowest_Expense_Transactions']}
Most Frequent Merchants: {analytics['most_frequent_merchant']}
"""
    prompt = f"""
You are an AI Personal Finance Assistant.

Analyze the financial statistics below.

Rules:
- Never perform calculations.
- Never change any numbers.
- Use only the provided statistics.
- Do not make assumptions about missing months or incomplete data.
- Do not mention categories unless they exist in the statistics.
- Provide the answer in the following format.

## Overall Financial Health

## Spending Pattern

## Income Analysis

## Monthly Trends

## Five Personalized Budgeting Suggestions

Financial Statistics:

{summary}
"""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = call_gemini_with_retry(payload, max_retries=3)

    if response.status_code != 200:
        return "Sorry, the AI service is temporarily busy. Please try again in a moment."

    result = response.json()
    answer = result["candidates"][0]["content"]["parts"][0]["text"]
    return answer


def ask_finance_question(user_question, analytics, df):
    prompt = f"""
You are an intent classification assistant.
Your job is NOT to answer the question.
Your job is ONLY to identify the user's intent.
Possible intents:
category_spending
total_income
total_expense
saving_rate
highest_expense
monthly_spending
monthly_income
monthly_saving
merchant_frequency
top_spending_merchants
Rules:
- Return ONLY valid JSON.
- Do NOT explain anything.
- Do NOT use markdown.
Examples:
Question:
How much did I spend on Food?
Output:
{{
"intent":"category_spending",
"category":"Food"
}}
Question:
What is my total income?
Output:
{{
"intent":"total_income"
}}
Question:
Show monthly spending
Output:
{{
"intent":"monthly_spending"
}}
Question:
How much did I spend in February?
Output:
{{
"intent":"monthly_spending",
"month":"February"
}}
Now classify this question:
{user_question}
"""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = call_gemini_with_retry(payload, max_retries=3)

    if response.status_code != 200:
        return "Sorry, AI service is unavailable."

    result = response.json()
    ans = result["candidates"][0]["content"]["parts"][0]["text"]

    try:
        ans = clean_json_response(ans)
        intent_data = json.loads(ans)
    except:
        return "Invalid AI response."

    intent = intent_data.get("intent")
    if intent is None:
        return "Sorry, I couldn't understand the question."

    if intent == "category_spending":
        category = intent_data.get("category")
        if category is None:
            return "Category not found."
        category = category.title()
        if category not in df["category"].unique():
            return f"I don't have any transactions in the '{category}' category. Available categories: {', '.join(df['category'].unique())}"
        amount = df[df["category"] == category]["amounts"].sum()
        return f"You spent ₹{amount} on {category}."

    elif intent == "total_income":
        return f"Your total income is ₹{analytics['total_credit']}."
    elif intent == "total_expense":
        return f"Your total expense is ₹{analytics['total_debit']}."
    elif intent == "saving_rate":
        return f"Your savings rate is {analytics['Savings_Rate']:.2f}%."
    elif intent == "highest_expense":
        return analytics['Top_5_Highest_Expense_Transactions'].to_string(index=False)
    elif intent == "monthly_income":
        return analytics['income'].to_string()
    elif intent == "monthly_saving":
        return analytics['Monthly_Saving_Analysis'].to_string()
    elif intent == "merchant_frequency":
        return analytics['most_frequent_merchant'].head(5).to_string()
    elif intent == "top_spending_merchants":
        return analytics['Top_Spending_Merchants'].head(5).to_string()
    elif intent == "monthly_spending":
        month = intent_data.get("month")
        if month:
            if month in analytics['Monthly_Spending_Analysis'].index:
                return f"You spent ₹{analytics['Monthly_Spending_Analysis'][month]} in {month}."
            else:
                return f"No spending data found for {month}."
        else:
            return analytics['Monthly_Spending_Analysis'].to_string()
    else:
        return "Sorry, I couldn't understand the question."