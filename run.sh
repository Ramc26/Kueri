#!/bin/bash

# Kueri Run Script
# Starts both the MCP server and Streamlit app

set -e

echo "🦉 Starting Kueri..."
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed."
    exit 1
fi

# Check if dependencies are installed
if [ ! -d ".venv" ]; then
    echo "⚠️  Dependencies not installed. Running install.sh first..."
    ./install.sh
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Please create it with your OPENAI_API_KEY"
    exit 1
fi

# Start server in background
echo "🚀 Starting MCP server on port 8001..."
uv run python server.py &
SERVER_PID=$!

# Wait a bit for server to start
sleep 3

# Check if server started successfully
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "❌ Server failed to start"
    exit 1
fi

echo "✅ Server started (PID: $SERVER_PID)"
echo ""

# Start Streamlit app
echo "🚀 Starting Streamlit app on port 8501..."
echo ""
echo "Open your browser to http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Trap Ctrl+C to kill both processes
trap "echo ''; echo '🛑 Stopping services...'; kill $SERVER_PID 2>/dev/null; exit" INT

uv run streamlit run app.py

# Cleanup on exit
kill $SERVER_PID 2>/dev/null

