#!/bin/bash

# Kueri Installation Script
# This script sets up the Kueri Text2SQL project

set -e  # Exit on error

echo "🦉 Kueri - Text2SQL Setup"
echo "=========================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed."
    echo "Please install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv is installed"
echo ""

# Check if project is already initialized
if [ ! -f "pyproject.toml" ]; then
    echo "📦 Initializing uv project..."
    uv init --no-readme
    echo "✅ Project initialized"
    echo "⚠️  Note: You may need to update pyproject.toml with your dependencies"
else
    echo "✅ Project already initialized (pyproject.toml exists)"
fi

echo ""

# Sync dependencies
echo "📥 Installing dependencies..."
uv sync
echo "✅ Dependencies installed"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating .env template..."
    cat > .env << EOF
# OpenAI API Key (required)
OPENAI_API_KEY=your_openai_api_key_here

# Database credentials can be stored in databases/*.json files
# Or use environment variables for passwords in JSON configs
EOF
    echo "✅ .env template created"
    echo "⚠️  Please update .env with your OpenAI API key"
    echo ""
fi

# Check for databases directory
if [ ! -d "databases" ]; then
    echo "📁 Creating databases directory..."
    mkdir -p databases
    echo "✅ Databases directory created"
    echo "⚠️  Please add database configuration files to databases/ directory"
    echo ""
fi

echo "=========================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your OPENAI_API_KEY"
echo "2. Add database configs to databases/ directory (see databases/_template.json)"
echo "3. Run the server: uv run python server.py"
echo "4. In another terminal, run the app: uv run streamlit run app.py"
echo ""
echo "Or use the run.sh script to start both services: ./run.sh"
echo ""

