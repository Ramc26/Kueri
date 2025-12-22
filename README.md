# Kueri - Text2SQL Chat Interface 🦉

Ever wondered if you could just ask your database questions in plain English? Well, wonder no more! Kueri is a smart chat interface that turns your natural language questions into SQL queries and gets you the answers you need.

## How It Works (The Fun Part)

Let's break down how this whole thing comes together, piece by piece:

### The Big Picture

You type a question → The AI agent figures out what you want → It explores your database → Generates SQL → Runs it → Shows you the results. Simple, right? Well, there's a bit more happening behind the scenes...

### 1. The Database Config (`db_config.json`) - Your Database's ID Card

Think of `db_config.json` as a cheat sheet that tells the system everything it needs to know about your databases. It's like a menu at a restaurant, but instead of food, it lists:

- **What each database contains**: Is it e-commerce stuff? Project management? Employee data?
- **Keywords**: Words that help the system figure out which database to use when you ask a question
- **Table descriptions**: What each table actually holds (so the AI doesn't have to guess)
- **Common queries**: Examples of what people usually ask

Why does this matter? Well, imagine you have multiple databases. When you ask "Show me all pending orders," the system needs to know:
- Which database has "orders"?
- What does "pending" mean in that context?
- What tables should it look at?

The config file answers all these questions upfront, making the AI's job way easier.

### 2. The Server (`server.py`) - The Middleman

`server.py` is like a helpful waiter in a restaurant. You don't talk directly to the kitchen (your databases), you talk to the waiter, and they handle everything.

Here's what it does:

- **Runs an MCP (Model Context Protocol) server**: This is basically a standardized way for AI agents to talk to tools
- **Exposes database tools**: It makes three main tools available:
  - `list_tables`: "Hey, what tables do you have?"
  - `get_table_schema`: "What columns are in this table?"
  - `run_sql_query`: "Run this SQL query and give me the results"
- **Handles HTTP requests**: The agent talks to the server via HTTP, and the server translates those requests into actual database operations

Think of it as a translator between the AI agent (who speaks "tool language") and your databases (who speak "SQL"). Without the server, they'd be talking past each other.

### 3. The Tools (`tools/db_tools.py`) - The Actual Workers

These are the functions that actually do the heavy lifting. Each tool is a simple, focused function:

- **`list_tables(db_key)`**: Connects to a database and lists all its tables. Simple, but essential for the AI to know what's available.
- **`get_table_schema(db_key, table_name)`**: Gets the structure of a specific table - column names, data types, etc. The AI needs this to write correct SQL.
- **`run_sql_query(db_key, query)`**: The big one. Takes a SQL query string, runs it against the database, and returns the results.

These tools are registered with the server (via `register_tools.py`), which makes them available to the AI agent. It's like giving the AI a toolbox with exactly the right tools for database work.

### 4. The Agent (`agent.py`) - The Brain

This is where the magic happens. The agent is built using LangGraph and OpenAI's GPT models. Here's its workflow:

1. **You ask a question** in the Streamlit app
2. **The agent receives it** and thinks: "What does this person want?"
3. **It uses the tools** to explore the database:
   - First, it might list tables to see what's available
   - Then it checks the schema of relevant tables
   - Finally, it constructs a SQL query based on what it learned
4. **It executes the query** using the `run_sql_query` tool
5. **It formats the results** and sends them back to you

The cool part? The agent is smart enough to:
- Figure out which database to use (with help from the config)
- Explore the schema before writing queries (so it doesn't make mistakes)
- Handle follow-up questions in a conversation
- Show you the SQL it generated (so you can verify it's correct)

### 5. The Chat Interface (`app.py`) - The Face

This is what you actually see and interact with. It's a Streamlit app that:

- Provides a chat interface (like ChatGPT, but for databases)
- Lets you select which database to query
- Shows your conversation history
- Displays the SQL queries the agent generated (in a collapsible section)
- Handles all the async stuff so everything runs smoothly

### The Flow (Step by Step)

1. **You type**: "Show me all pending orders"
2. **Streamlit app** sends this to the agent
3. **Agent** checks `db_config.json` to figure out which database has "orders"
4. **Agent** calls `list_tables` tool via the server to see what tables exist
5. **Agent** calls `get_table_schema` to understand the orders table structure
6. **Agent** generates SQL: `SELECT * FROM orders WHERE status = 'pending'`
7. **Agent** calls `run_sql_query` to execute it
8. **Results come back** through the server, to the agent, to the app, and finally to you
9. **You see** both the results AND the SQL query (so you know exactly what happened)

### Why This Architecture?

- **Separation of concerns**: Each piece has one job and does it well
- **Flexibility**: Want to add a new database? Just update the config. New tool? Add it to `db_tools.py`
- **Safety**: The server acts as a gatekeeper, so the agent can only do what the tools allow
- **Transparency**: You can see exactly what SQL was generated, so you're never in the dark

## In Summary

Kueri is basically a smart translator that:
- Understands your questions (thanks to GPT)
- Knows about your databases (thanks to `db_config.json`)
- Can explore and query them safely (thanks to the server and tools)
- Shows you everything it does (thanks to the chat interface)

It's like having a database expert who never sleeps, never gets tired, and always shows their work. Pretty neat, right? 🦉

