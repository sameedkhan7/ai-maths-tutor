# AI Maths Tutor – Friend's PC Setup Guide (Qwen 2.5 7B & Web App)

Yeh guide aapke dost ke laptop ya PC par AI Maths Tutor aur Qwen 2.5 7B chalane ke liye hai.

---

## ⚡ Sirf 3 Steps Mein Setup Karein:

### Step 1: Python Install Karein
* Agar PC par Python pehle se hai, toh bahut badhiya.
* Agar nahi hai, toh **[python.org](https://www.python.org/downloads/)** se Python 3.10 ya 3.11 download karein.
* **Important:** Install karte waqt **"Add Python to PATH"** checkbox zaroor tick karein!

### Step 2: Dependencies Install Karein
* Folder mein right-click karke **Open in Terminal / Command Prompt** karein aur run karein:
  ```bash
  pip install -r requirements.txt
  ```

### Step 3: Local Qwen 2.5 7B Run Karein (Apne RTX Graphic Card Par)
1. **[ollama.com/download](https://ollama.com/download)** se Ollama install karein.
2. Terminal mein bas ek command chalayein:
   ```bash
   ollama run qwen2.5:7b
   ```
   *(Yeh automatically 4.7 GB ka Qwen 2.5 model download karke aapke 8GB/12GB RTX GPU par load kar dega).*

---

## 🚀 App Run Karne Ka Tareeqa:

Folder mein bas **`start_tutor_with_qwen.bat`** par double click karein!
* Yeh apne aap backend engine aur local Qwen ko connect kar dega.
* Aur aapke default browser mein **`http://127.0.0.1:8000/login.html`** khol dega.

---

## 🔑 Login Accounts (Ready to Use):
Aap inme se kisi bhi account se login kar sakte hain:
* **Email:** `sameedkhan7@gmail.com` | **Password:** `1234`
* **Email:** `alex@gmail.com` | **Password:** `1234`
* **Email:** `dev@mathstutor.com` | **Password:** `admin`
* Ya fir **Sign Up** par click karke naya account bana sakte hain.

---

## 💡 Model Selector Feature:
* Chat window mein upar **Model Selector** button hai.
* Wahan se aap **"💻 Local RTX · Qwen 2.5 (7B GPU)"** select kar sakte hain jo aapke graphic card par 100% offline aur superfast chalega.
* Agar kabhi Ollama band ho, toh yeh automatically cloud AI par fallback kar leta hai!
