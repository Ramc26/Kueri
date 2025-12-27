# Dockerfile for Kueri
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files first (for better caching)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy project files
COPY . .

# Expose ports
# 8001 for MCP server
# 8501 for Streamlit
EXPOSE 8001 8501

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🦉 Starting Kueri..."\n\
echo "🚀 Starting MCP server on port 8001..."\n\
uv run python server.py &\n\
SERVER_PID=$!\n\
sleep 3\n\
echo "✅ Server started (PID: $SERVER_PID)"\n\
echo "🚀 Starting Streamlit app on port 8501..."\n\
echo "Open your browser to http://localhost:8501"\n\
trap "kill $SERVER_PID" EXIT\n\
uv run streamlit run app.py --server.port=8501 --server.address=0.0.0.0\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run startup script
CMD ["/app/start.sh"]

