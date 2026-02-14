#!/bin/bash
# Launch VOLT Trading Dashboard

echo "🚀 Launching VOLT Trading Dashboard..."
echo ""

# Check if in correct directory
if [ ! -f "dashboard/app.py" ]; then
    echo "❌ Error: Must run from VOLT-trading root directory"
    exit 1
fi

# Activate venv if exists
if [ -d ".venv" ]; then
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  Streamlit not found. Installing..."
    pip install streamlit plotly -q
fi

echo "📊 Starting dashboard on http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Launch Streamlit
streamlit run dashboard/app.py
