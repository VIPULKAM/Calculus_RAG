#!/bin/bash
# Quick launcher for Calculus RAG Streamlit app

echo "🧮 Starting Calculus Tutor..."
echo ""
echo "📱 The app will open in your browser at: http://localhost:8501"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run Streamlit
streamlit run app.py
