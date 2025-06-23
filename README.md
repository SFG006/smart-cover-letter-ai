# 📄 Smart Cover Letter Generator

A Flask web app that generates **personalized, professional cover letters** using your uploaded resume and a job description — powered by **Gemini AI (Google Generative AI)**.

![screenshot](https://your-screenshot-link-if-any.com)

---

## 📸 Live Demo

👉 Try it now on [Hugging Face Spaces](https://huggingface.co/spaces/SFG006/smart-cover-letter-ai)


---

## 🚀 Features

- 🔐 Upload your **PDF Resume**
- 🧠 Paste any **Job Description**
- 🧾 Instantly receive a **well-written cover letter** tailored to the job
- ⚙️ Validates email, phone, GitHub, LinkedIn inputs
- ✨ Powered by **Gemini 1.5 Flash** for fast, smart content generation
- 💡 Mobile-friendly, clean Bootstrap UI

---

## 🧠 How It Works

1. **Upload** your resume (PDF format).
2. **Paste** the full job description.
3. Fill in optional details like email, phone, GitHub, LinkedIn.
4. Click **"Generate Cover Letter"**.
5. The app sends all this data to **Gemini AI**, which responds with a natural-sounding, customized letter.
6. You can copy the result to clipboard instantly.

---

## 🖥️ Tech Stack

| Tech               | Use                  |
|--------------------|----------------------|
| 🐍 Python          | Backend logic         |
| 🔥 Flask           | Web framework         |
| 🧠 Gemini AI       | Text generation       |
| 📄 pdfplumber      | PDF text extraction   |
| 🎨 Bootstrap 5     | Styling               |
| 🌍 Jinja2          | Templating engine     |
| ☁️ Hugging Face/Render | Deployment-ready   |

---

## 📦 Setup Instructions

### 🔧 1. Clone the repo

```bash
git clone https://github.com/SFG006/smart-cover-letter-ai.git
cd smart-cover-letter-generator
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
│   └── style.css        # Optional styling
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

---

## 🤝 Acknowledgements

* Google Gemini API
* pdfplumber
* Bootstrap

---

## 💡 Future Improvements

* ✍️ Allow editing before downloading the letter
* 🗂 Save previous letters
* 🌐 Add multi-language support
* 📬 Export to PDF

---

## 🧑‍💻 Author

Made by **Shivansh Gupta**

---

## 📜 License

This project is licensed under the **MIT License**.
