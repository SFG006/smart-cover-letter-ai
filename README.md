# 📄 Smart Cover Letter AI

A Flask web app that generates **personalized, professional cover letters** using your uploaded resume and a job description — powered by **Gemini AI**.

![Cover_letter_image](https://github.com/user-attachments/assets/b7e0b684-3243-4aeb-83f2-705877a0acff)

---

## 🚀 Live

Try the app online on [Hugging Face Spaces](https://huggingface.co/spaces/SFG006/smart-cover-letter-ai)🤗

---

## 🛠️ Key Features

* 📄 Accepts and processes **PDF resumes** using robust backend parsing
* 🧠 Accepts any **job description** and intelligently maps it to your experience
* ✍️ Generates a **customized, professional cover letter** in real-time
* 🔍 Performs validation on essential fields (email, phone, GitHub, LinkedIn)
* ⚡ Integrates with **Gemini 2.5 Flash API** for fast, high-quality text generation
* 🧩 Built with a simple web interface to test and deploy functionality quickly

---

## 🧠 How It Works

1. **Upload** your resume (PDF format).
2. **Paste** the full job description.
3. Fill in optional details like email, phone, GitHub, LinkedIn.
4. Click **"Generate Cover Letter"**.
5. The app sends all this data to **Gemini AI**, which responds with a natural-sounding, customized letter.
6. You can copy the result to clipboard instantly.

---

## 🧱 Tech Stack

| Tool / Library          | Purpose                          |
| ----------------------- | -------------------------------- |
| 🐍 Python               | Core backend language            |
| 🔥 Flask                | Lightweight web framework        |
| 🧠 Gemini 2.5 Flash API | AI-powered text generation       |
| 📄 pdfplumber           | PDF text extraction              |
| ☁️ Hugging Face Spaces  | Deployment and testing interface |

---

## 📦 Setup Instructions

### 🔧 1. Clone the repo

```bash
git clone https://github.com/SFG006/smart-cover-letter-ai.git
cd smart-cover-letter-ai
````

### 🔑 2. Add your Google Gemini API Key

Create a `.env` file or set an environment variable:

```bash
export GOOGLE_API_KEY=your_api_key_here
```

### ▶️ 3. Run the Flask app

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:7860` to use the app locally.

---

## 📁 Folder Structure

```
smart-cover-letter-generator/
│
├── app.py               # Main Flask app
├── templates/
│   └── index.html       # Jinja2 template
├── static/
│   └── style.css        # styling
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## 🧑‍💻 Author

Made by **Shivansh Gupta**

---

## 📜 License

This project is licensed under the **MIT License**.
