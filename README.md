![Kueri Logo](Logos/LogoLand.png)

# 🦉 Kueri: Because Writing SQL is Hard.

Welcome to **Kueri**. It's a Text2SQL interface for people who have better things to do than remember if it's `LEFT JOIN` or `RIGHT JOIN`.

I started this project, ignored it for a century, and finally resurrected it. It’s alive! (And it actually works).

---

## 🛠️ The Architecture (The "How it works" Bit)

| Component | What it thinks it is | What it actually is |
| --- | --- | --- |
| **`db_config.json`** | The Master Config | Shared settings and guidelines that apply to all databases. |
| **`databases/*.json`** | Individual DB Configs | One JSON file per database. Add/remove databases by adding/removing files. |
| **`server.py`** | MCP Server | An overpriced waiter (the middleman). |
| **`tools/`** | Specialized Workers | A hammer, a flashlight, and a magnifying glass. |
| **`agent.py`** | The "Brain" | LangGraph + GPT having a conversation with your data. |
| **`app.py`** | The UI | A pretty Streamlit face for messy code. |

---

## 🧐 The Breakdown

### 1. `db_config.json` + `databases/*.json` — The Modular Cheat Sheet

**`db_config.json`** contains shared settings that apply to all databases:
* **Selection Guidelines:** How the AI should choose which database to use
* **Default Settings:** Global settings like query timeouts, logging, etc.

**`databases/*.json`** — Each database gets its own file! This is the modular part:
* **Add a database:** Just drop a new JSON file in `databases/` folder
* **Remove a database:** Delete the JSON file
* **No editing the main config:** Each DB is self-contained

Each database JSON file contains:
* **Bio:** What is this DB for? (Sales? Employees? Secrets?)
* **Interests:** Keywords to help the AI find it.
* **Inside Info:** Table descriptions so the AI doesn't have to guess.
* **Standard Orders:** Example queries for when the AI feels uninspired.
* **Environment Key:** Which env variable holds the connection string.

### 2. `server.py` — The Waiter

This runs the **Model Context Protocol (MCP)**.

* It stands between the AI and your precious data.
* The AI says: "I want to see tables."
* The Waiter says: "Hold on, let me check the kitchen."
* It makes sure the AI doesn't try to order something that isn't on the menu.

### 3. `tools/db_tools.py` — The Muscle

Actual Python functions doing the dirty work:

* `list_tables`: "What’s in the box?"
* `get_table_schema`: "How is the box organized?"
* `run_sql_query`: "Actually open the box and get the data."

### 4. `agent.py` — The "Genius" 🧠

Powered by **LangGraph** and **OpenAI**.

1. **Hears your question.** (e.g., *"Who bought the most coffee?"*)
2. **Panics slightly.** 3.  **Checks the config.** (Finds the 'Sales' DB).
3. **Checks the tables.** (Finds 'Customers' and 'Orders').
4. **Writes SQL.** (Praying it works).
5. **Runs it.** 7.  **Acts like it knew the answer all along.**

### 5. `app.py` — The Pretty Face 💅

A **Streamlit** interface that keeps things simple:

* Chat like you're talking to a human.
* Sneak a peek at the SQL (if you don't trust the AI).
* Watch your data come back without touching a semicolon.

---

## 🔄 The Flow (In Simple English)

1. **You:** "Who are my top 5 customers?"
2. **Kueri:** *Consults the ancient scrolls (JSON config).*
3. **Kueri:** *Asks the waiter (MCP) for the table list.*
4. **Kueri:** *Writes a SQL query that would take you 10 minutes to type.*
5. **Kueri:** *Executes it and shows you a table.*
6. **You:** *Look smart in front of your boss.*

---

## 🏆 Why use Kueri?

* **Zero SQL Knowledge Needed:** Great for managers.
* **Safety First:** The AI only sees what the tools show it.
* **Lazy Friendly:** Just update the JSON and you're done.
* **Resurrection Proof:** Even if you leave it for 100 years, it still works.

---

> **Note:** No databases were harmed in the making of this app. Only my sleep schedule.

---

<div style="text-align: center; color: #888;">
Resurrected from the "I'll finish this later" folder after 100 years by <a href='[https://ramc26.github.io/RamTechSuite](https://ramc26.github.io/RamTechSuite)' target='_blank' style='color: #EAAA00; text-decoration: none;'>🦉 <strong>RamBikkina</strong></a>
</div>
