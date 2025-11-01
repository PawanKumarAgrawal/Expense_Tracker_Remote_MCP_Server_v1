# pip install fastmcp

from fastmcp import FastMCP
import sqlite3
import os
import json

# Create MCP server
mcp = FastMCP("Expense Tracker v1 (Synchronus)")

# Safe database location (writable on MCP Cloud)
DB_PATH = os.path.join(os.getcwd(), "expenses.db")
CATEGORIES_PATH = os.path.join(os.getcwd(), "categories.json")


def init_database():
    """Initialize the database with expenses table."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            sub_category TEXT,
            note TEXT
        )
    ''')
    conn.commit()
    conn.close()


# Initialize database when server starts
init_database()


@mcp.tool()
def add_expense(date: str, amount: float, category: str, sub_category: str = "", note: str = "") -> str:
    """Add a new expense entry to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO expenses (date, amount, category, sub_category, note)
            VALUES (?, ?, ?, ?, ?)
        ''', (date, amount, category, sub_category, note))
        conn.commit()
        return f"✅ Added: {amount} for {category} ({date})"
    except Exception as e:
        return f"❌ Failed to add expense: {e}"
    finally:
        conn.close()


@mcp.tool()
def list_expenses_by_date(start_date: str, end_date: str) -> str:
    """List expense entries within a specific date range."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT date, amount, category, sub_category, note 
        FROM expenses 
        WHERE date BETWEEN ? AND ?
        ORDER BY date DESC
    ''', (start_date, end_date))

    expenses = cursor.fetchall()
    conn.close()

    if not expenses:
        return f"No expenses found between {start_date} and {end_date}."

    result = [f"Expenses from {start_date} to {end_date}:"]
    total = 0
    for date, amount, category, sub_category, note in expenses:
        total += amount
        entry = f"- {date}: {amount} ({category}"
        if sub_category:
            entry += f" → {sub_category}"
        if note:
            entry += f" | {note}"
        entry += ")"
        result.append(entry)

    result.append(f"\nTotal: {total}")
    return "\n".join(result)


@mcp.tool()
def summarize_expenses(start_date: str, end_date: str, category: str = None) -> str:
    """Summarize expenses by category within a date range."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if category:
        cursor.execute('''
            SELECT SUM(amount) as total
            FROM expenses 
            WHERE date BETWEEN ? AND ? AND category = ?
        ''', (start_date, end_date, category))
        total = cursor.fetchone()[0]
        conn.close()
        return f"Total for {category}: {total or 0} between {start_date} and {end_date}"
    else:
        cursor.execute('''
            SELECT category, SUM(amount) as total
            FROM expenses 
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total DESC
        ''', (start_date, end_date))
        results = cursor.fetchall()
        conn.close()

        if not results:
            return f"No expenses found between {start_date} and {end_date}."

        summary = [f"Expense summary from {start_date} to {end_date}:"]
        grand_total = 0
        for cat, total in results:
            summary.append(f"- {cat}: {total}")
            grand_total += total
        summary.append(f"\nGrand Total: {grand_total}")
        return "\n".join(summary)


# Category resource
@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """Provide category→subcategory mapping."""
    if not os.path.exists(CATEGORIES_PATH):
        # Default file if missing
        default_data = {
            "Food": ["Groceries", "Dining Out"],
            "Transport": ["Fuel", "Public Transit"],
            "Utilities": ["Electricity", "Water", "Internet"]
        }
        with open(CATEGORIES_PATH, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2)

    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# Key difference for remote server: Use HTTP transport
if __name__ == "__main__":
    
    print(f"✅ Database Path: {DB_PATH}")
    print(f"✅ Categories Path: {CATEGORIES_PATH}")
    
    mcp.run(transport="http", host="0.0.0.0", port=8000)
