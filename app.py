import streamlit as st
import asyncio
import json
import base64
from pathlib import Path
from datetime import datetime
from agent import SQLAgent
from loguru import logger

# Page config
st.set_page_config(
    page_title="Kueri",
    page_icon="Logos/LogoFinal.png",
    layout="wide"
)

# Load database configs
@st.cache_data
def load_db_config():
    """Load main config file"""
    with open("db_config.json", "r") as f:
        return json.load(f)

@st.cache_data
def load_all_databases():
    """Dynamically load all database configs from databases/ directory"""
    config = load_db_config()
    databases_dir = Path(config.get("databases_directory", "databases"))
    
    databases = {}
    if databases_dir.exists():
        for db_file in databases_dir.glob("*.json"):
            # Skip template file
            if db_file.name.startswith("_"):
                continue
            try:
                with open(db_file, "r") as f:
                    db_config = json.load(f)
                    # Get db_key from metadata if new structure, otherwise from root
                    metadata = db_config.get("metadata", {})
                    db_key = metadata.get("db_key") if metadata else db_config.get("db_key", db_file.stem)
                    databases[db_key] = db_config
            except Exception as e:
                logger.warning(f"Failed to load {db_file}: {e}")
    
    return databases

db_config = load_db_config()
all_databases = load_all_databases()

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
    st.title("Config")
    
    # Database selection
    db_options = {}
    for db_key, db_info in all_databases.items():
        metadata = db_info.get("metadata", {})
        actual_db_key = metadata.get("db_key", db_key)
        db_options[actual_db_key] = {
            "name": metadata.get("name", db_key),
            "description": metadata.get("description", ""),
            "db_key": actual_db_key
        }
    
    if not db_options:
        st.warning("No databases configured. Add JSON files to the 'databases/' directory.")
        selected_db = None
    else:
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
        for db_key, db_info in all_databases.items():
            metadata = db_info.get("metadata", {})
            st.caption(f"• **{metadata.get('name', db_key)}**: {metadata.get('description', '')}")

# Main chat interface
# Remove top padding/margin to move logo to top
st.markdown("""
    <style>
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .stApp > header {
            visibility: hidden;
        }
        .stApp {
            margin-top: 0px;
        }
    </style>
""", unsafe_allow_html=True)

# Load and display logo with HTML/CSS for percentage sizing
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_path = Path("Logos/LogoLand.png")
if logo_path.exists():
    logo_base64 = get_base64_image(logo_path)
    st.markdown(
        f'<div style="text-align: center; margin-top: 0; padding-top: 0;"><img src="data:image/png;base64,{logo_base64}" style="width: 60%; max-width: 600px; height: auto;"></div>',
        unsafe_allow_html=True
    )
else:
    st.image("Logos/LogoLand.png", width=600)

st.markdown("Ask questions in natural language and get SQL query results!")

# Display chat history
for message in st.session_state.messages:
    # Set avatar based on message role
    avatar = None
    if message["role"] == "assistant":
        avatar_path = Path("Logos/LogoFinal.png")
        if avatar_path.exists():
            avatar = str(avatar_path)
    elif message["role"] == "user":
        avatar_path = Path("Logos/LogoUser.png")
        if avatar_path.exists():
            avatar = str(avatar_path)
    
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        # Display timestamp
        timestamp = message.get("timestamp", "")
        if timestamp:
            st.caption(f"🕐 {timestamp}")
        # Show SQL query dropdown for assistant messages
        if message["role"] == "assistant" and message.get("sql_query"):
            with st.expander("🔍 View SQL Query", expanded=False):
                st.code(message["sql_query"], language="sql")

# Chat input
if prompt := st.chat_input("Ask a question about your database..."):
    if not selected_db:
        st.error("Please select a database from the sidebar first.")
    else:
        # Get current timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add user message to chat with timestamp
        user_message = {
            "role": "user",
            "content": prompt,
            "timestamp": current_time
        }
        st.session_state.messages.append(user_message)
        
        # Set user avatar
        user_avatar_path = Path("Logos/LogoUser.png")
        user_avatar = str(user_avatar_path) if user_avatar_path.exists() else None
        
        with st.chat_message("user", avatar=user_avatar):
            st.markdown(prompt)
            st.caption(f"🕐 {current_time}")
        
        # Get agent response
        avatar_path = Path("Logos/LogoFinal.png")
        avatar = str(avatar_path) if avatar_path.exists() else None
        
        with st.chat_message("assistant", avatar=avatar):
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
                    
                    # Display timestamp for assistant message
                    assistant_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.caption(f"🕐 {assistant_time}")
                    
                    # Show SQL query in expander
                    if sql_query:
                        with st.expander("🔍 View SQL Query", expanded=False):
                            st.code(sql_query, language="sql")
                    
                    # Store message with SQL query and timestamp
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result_text,
                        "sql_query": sql_query,
                        "timestamp": assistant_time
                    })
                except Exception as e:
                    error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.caption(f"🕐 {error_time}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sql_query": None,
                        "timestamp": error_time
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