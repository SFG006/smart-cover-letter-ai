from flask import Flask, render_template , request , abort , redirect, url_for, session
from werkzeug.utils import secure_filename
import pdfplumber
import requests
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 7 * 1024 * 1024  # 7MB file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.secret_key = os.urandom(24)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Function to check file is pdf format or not
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Function to extract text from PDF
def extract_txt(pdf_file):
    """Extract text from PDF file with improved error handling"""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except pdfplumber.PDFSyntaxError:
        raise ValueError("Invalid PDF file")
    except Exception as e:
        raise RuntimeError(f"❌ Failed to extract text from PDF: {str(e)}")

# Generate Cover Letter
def generate_cover_letter(resume_text, job_text):
    """Generate cover letter with robust API handling"""
    if not resume_text and not job_text:
        raise ValueError("Missing required input")
    # Prepare the prompt
    prompt = f"""You are a professional cover letter writing assistant AI.

    Your job is to take the following resume and job description and write a fully personalized, complete, and professional cover letter. Use strong formatting, confident language, and ensure there are **no placeholders** left.

    ---

    ### Resume:
    {resume_text}

    ---

    ### Job Description:
    {job_text}

    ---

    ### Output Instructions:
    - Always start the letter with this contact block:
      **Shivansh Gupta**  
      shivanshg005@gmail.com | +91 6306550271  
      [GitHub](https://github.com/shivanshgupta005) | [LinkedIn](https://linkedin.com/in/shivanshgupta005)

    - Add the **current date** automatically.
    - Invent realistic company name and address based on the job description, if not given.
    - Use the subject line: **Application for [Job Title] Position** — inferred from the job description.
    - In the body:
      - Start with an enthusiastic introduction about the job
      - Highlight 1–2 projects from the resume that are most relevant
      - Emphasize relevant tech stacks and tools (Python, Flask, Docker, etc.)
      - Mention any creative or soft skills from the resume (e.g., video editing)
    - Close with a confident call to action and professional sign-off.
    - Keep formatting clean and formal (with bold headings where needed).
    - Do **not** generate anything beyond the cover letter.

    Now, write the full professional cover letter based on the above.
    Keep your writing structured, polite, and similar to a real-world corporate application letter, not overly creative or abstract.
    """

    result = None # Default value

    # To check API key exists
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("API key not found in environment variables!")


    # Prepare headers and payload
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8080",  # required by OpenRouter
        "X-Title": "Cover Letter Generator"
    }

    payload = {
        "model": "deepseek/deepseek-chat-v3-0324",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that writes cover letters."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "top_p": 0.8,
        "max_tokens": 500,
        "do_sample": True,
        "repetition_penalty": 1.1
    }



    try:
        # Send the request to API
        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                 headers=headers,
                                 json=payload,
                                 timeout=30
                                 )
        response.raise_for_status()    ## Raise error if response code is not 200
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out. Try again later.")
        return "Request timed out."
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"API request failed: {str(e)}")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Validate inputs
            if "resume" not in request.files:
                abort(400,"No resume file uploaded")

            # Get uploaded resume PDF
            resume_file = request.files["resume"]
            job_text = request.form.get("job_description",'').strip()

            if resume_file.filename == '':
                abort(400,"No selected file")
            if not allowed_file(resume_file.filename):
                abort(400,"Only PDF files are allowed")
            if len(job_text) < 20:
                abort(400,"Job description is too short (min 20 characters)")

            # Process in memory without saving
            resume_text = extract_txt(resume_file.stream)
            cover_letter = generate_cover_letter(resume_text, job_text)
            session["cover_letter"] = cover_letter
            return redirect(url_for("index"))
        except ValueError as e:
            abort(400,str(e))
        except RuntimeError as e:
            abort(503,str(e))
        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            abort(500, "Internal server error")
        # Render the GET page
    cover_letter = session.pop("cover_letter", None)  # get once, then clear
    return render_template("index.html", result = cover_letter)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
