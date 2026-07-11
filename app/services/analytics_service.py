import pandas as pd

def compute_analytics(df):
    total_debit = df[df["types"] == "debit"]["amounts"].sum()
    total_credit = df[df["types"] == "credit"]["amounts"].sum()
    net_balance = total_credit - total_debit
    Average_Debit_Transaction_Amount = df[df["types"] == "debit"]["amounts"].mean()
    df["dates"] = pd.to_datetime(df["dates"])
    df["month"] = df["dates"].dt.strftime("%B")
    Monthly_Spending_Analysis = df[df["types"] == "debit"].groupby("month")["amounts"].sum()
    Monthly_Saving_Analysis = df[df["types"] == "credit"].groupby("month")["amounts"].sum() - Monthly_Spending_Analysis
    income = df[df["types"] == "credit"].groupby("month")["amounts"].sum()
    Average_Monthly_Spending = df[df["types"] == "debit"].groupby("month")["amounts"].mean()
    Top_5_Highest_Expense_Transactions = df[df["types"] == "debit"].sort_values(by="amounts", ascending=False).head(5)
    Top_3_Lowest_Expense_Transactions = df[df["types"] == "debit"].sort_values(by="amounts").head(3)
    Transaction_Type_Distribution = df["types"].value_counts()
    Savings_Rate = (df[df["types"] == "credit"]["amounts"].sum() - df[df["types"] == "debit"]["amounts"].sum()) / df[df["types"] == "credit"]["amounts"].sum() * 100
    spend = df[df["types"] == "debit"].groupby("month")["amounts"].sum()
    saving = income - spend
    most_frequent_merchant = df[df["types"] == "debit"].groupby("descriptions")["descriptions"].count().sort_values(ascending=False)
    Top_Spending_Merchants = df[df["types"] == "debit"].groupby("descriptions")["amounts"].sum().sort_values(ascending=False)

    return {
        "total_debit": total_debit,
        "total_credit": total_credit,
        "net_balance": net_balance,
        "Average_Debit_Transaction_Amount": Average_Debit_Transaction_Amount,
        "Monthly_Spending_Analysis": Monthly_Spending_Analysis,
        "Monthly_Saving_Analysis": Monthly_Saving_Analysis,
        "Average_Monthly_Spending": Average_Monthly_Spending,
        "Top_5_Highest_Expense_Transactions": Top_5_Highest_Expense_Transactions,
        "Top_3_Lowest_Expense_Transactions": Top_3_Lowest_Expense_Transactions,
        "Savings_Rate": Savings_Rate,
        "spend": spend,
        "income": income,
        "saving": saving,
        "most_frequent_merchant": most_frequent_merchant,
        "Top_Spending_Merchants": Top_Spending_Merchants,
    }