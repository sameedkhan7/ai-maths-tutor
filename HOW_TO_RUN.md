# 🎓 AI Maths Tutor - Setup & Run Guide (For Friend)

Namaste! This is the complete **AI Maths Tutor** project. Follow these simple steps to run it on your laptop/computer.

---

### 🚀 Quick Start (Easiest Way - 1 Click!)

1. **Double-click `start_backend.bat`** (or `start_all_servers.bat`).
   - It will automatically install any required Python packages and launch the FastAPI AI server on `http://127.0.0.1:8000`.
2. Open your browser and go to:
   - **`http://127.0.0.1:5500/login.html`** (or just open `maths.html` in your browser / Live Server).

---

### 💻 Manual Step-by-Step Setup (If preferred)

#### Step 1: Install Dependencies
Open Terminal / Command Prompt in this project folder and run:
```bash
pip install -r backend/requirements.txt
```

#### Step 2: Set API Key (.env)
Check the `.env` file in the root folder. It already has the API key pre-configured:
```env
GROQ_API_KEY='your_groq_api_key'
GROQ_MODEL='openai/gpt-oss-120b'
```
*(If you have your own Groq API key, you can replace it anytime at [console.groq.com](https://console.groq.com)).*

#### Step 3: Run the Backend
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```
Backend will start on: `http://127.0.0.1:8000`  
Swagger API Docs: `http://127.0.0.1:8000/docs`

#### Step 4: Run the Frontend
In another terminal in the root project folder:
```bash
python -m http.server 5500
```
Now open:
👉 **`http://127.0.0.1:5500/login.html`** or **`http://127.0.0.1:5500/maths.html`**

---

### 🗄️ Database Note
- By default, the system uses the included **SQLite database (`tutor.db`)** so you do **NOT** need to install or configure MySQL.
- If you have MySQL installed, it will automatically connect if credentials match `.env`.

---

### ✨ Features Included
- 📐 **Interactive Trigonometry & Geometry Visualizer** (Automatic SVG Generation)
- 🏏 **Sports Mode / Cricket Analogy** (Real-life visual examples)
- 🎙️ **Voice AI Tutor** (Text-to-speech)
- 📚 **NCERT Class 10/11/12 Maths Context & RAG**
- 💬 **Multiple Learning Styles**: Quick Answer, Step-by-Step, Story Mode, Sports Mode
