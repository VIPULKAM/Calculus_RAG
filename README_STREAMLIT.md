# 🧮 Calculus Tutor - Streamlit App

## Beautiful Math Rendering - Problem Solved! ✅

Your LaTeX equations now render as **beautiful mathematical notation** - just like in textbooks!

---

## 🚀 Quick Start

### 1. Make sure the database is running:
```bash
docker-compose up -d postgres
```

### 2. Launch the app:
```bash
./run_app.sh
```

Or manually:
```bash
source .venv/bin/activate
streamlit run app.py
```

### 3. Open in browser:
The app will automatically open at: **http://localhost:8501**

---

## ✨ Before & After

### ❌ Before (Terminal):
```
The derivative is $\frac{dy}{dx} = 2x$
```
Raw LaTeX code - hard to read!

### ✅ After (Streamlit):
```
The derivative is dy/dx = 2x
```
**Beautifully rendered** with proper fractions, symbols, and formatting!

---

## 💡 How to Use

1. **Type your question** in the chat input at the bottom
2. **View the answer** with beautiful math rendering
3. **Check sources** - click "View Sources" to see which PDFs were used
4. **Adjust creativity** - use the sidebar slider to control response style
5. **Try examples** - click example questions in the sidebar

### Example Questions:
- "What is a derivative?"
- "Explain the chain rule step by step"
- "Solve x² + 5x + 6 = 0"
- "What is the limit definition?"
- "How do I integrate by parts?"

---

## 🎨 Features

✅ **Beautiful LaTeX Rendering**
- Fractions: dy/dx rendered properly
- Limits: lim(x→a) with subscripts
- Integrals, derivatives, summations all render perfectly

✅ **Smart AI Routing**
- Fast model (1.5B) for simple questions
- Powerful model (7B) for complex proofs
- Automatic fallback for reliability

✅ **Interactive UI**
- Chat history persists during session
- Source citations with relevance scores
- One-click example questions
- Adjustable temperature/creativity

✅ **Full Knowledge Base**
- 6,835 chunks from 17 PDFs + 44 Khan Academy videos
- Paul's Online Notes & Khan Academy summaries
- Calculus cheat sheets & reference materials
- Practice problems & study guides

---

## 🐛 Troubleshooting

### Database connection error
```bash
# Make sure PostgreSQL is running
docker-compose up -d postgres

# Verify it's accessible
psql -h localhost -U calculus_user -d calculus_db -c "SELECT COUNT(*) FROM calculus_knowledge"
```

### Ollama not responding
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Pull models if needed
ollama pull qwen2-math:1.5b
ollama pull qwen2-math:7b
ollama pull mxbai-embed-large
```

### Math not rendering
- Refresh the browser page
- Clear browser cache
- Check browser console for errors (F12)

### App is slow
- First question is always slower (model warmup)
- Complex questions use the larger 7B model (takes longer)
- Check your Ollama logs for issues

---

## 🔧 Technical Details

- **Frontend**: Streamlit with native MathJax rendering
- **Backend**: RAG pipeline (no changes needed!)
- **Models**: Qwen2-Math 1.5B + 7B with smart routing
- **Database**: PostgreSQL + pgvector
- **Embeddings**: mxbai-embed-large (1024d)

---

## 🎓 Perfect for Students!

High school students will love this because:
- 📖 Math looks like their textbooks
- 💬 Familiar chat interface
- 🎯 Example questions help them start
- 📚 Sources encourage verification
- 🚀 Fast, interactive responses

---

## 📊 Comparison

| Feature | Terminal | Streamlit |
|---------|----------|-----------|
| Math Rendering | ❌ Raw LaTeX | ✅ Beautiful |
| User Interface | ❌ Plain text | ✅ Web UI |
| Chat History | ❌ Scrolls away | ✅ Persistent |
| Examples | ❌ Manual | ✅ One-click |
| Mobile Friendly | ❌ No | ✅ Yes |

---

**Your LaTeX rendering problem is now solved!** 🎉

Ask questions and watch them render beautifully!
