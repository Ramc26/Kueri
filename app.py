import streamlit as st
import asyncio
import json
from agent import SQLAgent
from loguru import logger

# Page config
st.set_page_config(
    page_title="Kueri",
    page_icon="💬",
    layout="wide"
)

# Load database config
@st.cache_data
def load_db_config():
    with open("db_config.json", "r") as f:
        return json.load(f)

db_config = load_db_config()

# Initialize agent in session state
@st.cache_resource
def get_agent():
    return SQLAgent()

# Initialize agent
if "agent" not in st.session_state:
    st.session_state.agent = get_agent()
    st.session_state.agent_initialized = False

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize agent async
async def init_agent():
    if not st.session_state.agent_initialized:
        await st.session_state.agent.initialize()
        st.session_state.agent_initialized = True

# Run initialization
if not st.session_state.agent_initialized:
    with st.spinner("Initializing agent..."):
        asyncio.run(init_agent())

# Sidebar for database selection
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Database selection
    db_options = {}
    for db_key, db_info in db_config["databases"].items():
        env_key = f"{db_key.upper().replace('_DB', '_DB_URL')}"
        db_options[env_key] = {
            "name": db_info["name"],
            "description": db_info["description"]
        }
    
    selected_db = st.selectbox(
        "Select Database",
        options=list(db_options.keys()),
        format_func=lambda x: db_options[x]["name"],
        help="Choose which database to query"
    )
    
    st.markdown("---")
    st.markdown(f"**Description:**")
    st.caption(db_options[selected_db]["description"])
    
    st.markdown("---")
    st.markdown("**Available Databases:**")
    for db_key, db_info in db_config["databases"].items():
        with st.expander(db_info["name"]):
            st.markdown(f"**Keywords:** {', '.join(db_info['keywords'][:5])}...")
            st.markdown("**Tables:**")
            for table, desc in db_info["tables"].items():
                st.caption(f"• {table}: {desc}")

# Main chat interface
st.title("💬 Kueri")
st.markdown("Ask questions in natural language and get SQL query results!")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Show SQL query dropdown for assistant messages
        if message["role"] == "assistant" and message.get("sql_query"):
            with st.expander("🔍 View SQL Query", expanded=False):
                st.code(message["sql_query"], language="sql")

# Chat input
if prompt := st.chat_input("Ask a question about your database..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Run async query
                response = asyncio.run(
                    st.session_state.agent.query(prompt, db_key=selected_db)
                )
                # Handle both dict (new format) and string (old format) responses
                if isinstance(response, dict):
                    result_text = response.get("result", "")
                    sql_query = response.get("sql_query")
                else:
                    result_text = response
                    sql_query = None
                
                st.markdown(result_text)
                
                # Show SQL query in expander
                if sql_query:
                    with st.expander("🔍 View SQL Query", expanded=False):
                        st.code(sql_query, language="sql")
                
                # Store message with SQL query
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result_text,
                    "sql_query": sql_query
                })
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "sql_query": None
                })
                logger.error(f"Query failed: {e}")

# Clear chat button
if st.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Minimal Sticky Footer
footer_content = """
<style>
    .reportview-container .main footer {visibility: hidden;}    /* Hide default footer */
    
    .sticky-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(14, 17, 23, 0.85); /* Semi-transparent dark to blend in */
        backdrop-filter: blur(5px);
        color: ivory;
        text-align: center;
        padding: 8px 0;
        font-size: 0.85rem;
        border-top: 1px solid rgba(250, 250, 250, 0.1);
        z-index: 999;
    }
    
    .sticky-footer strong {
        color: #EAAA00;
    }
    
    /* Ensure content doesn't get cut off at the bottom */
    .footer-spacer {
        margin-bottom: 60px;
    }
</style>

<div class="footer-spacer"></div>
<div class="sticky-footer">
    Resurrected from the "I'll finish this later" folder after 100 years by <a href='https://ramc26.github.io/RamTechSuite' target='_blank' style='color: inherit; text-decoration: none;'>🦉 <strong>RamBikkina</strong></a>
</div>
"""

st.markdown(footer_content, unsafe_allow_html=True)