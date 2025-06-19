from flask import Flask, render_template , request , abort
from werkzeug.utils import secure_filename
import pdfplumber
import requests
import os
from dotenv import load_dotenv
from markupsafe import escape

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 7 * 1024 * 1024  # 7MB file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

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
    prompt =f"""You are a professional cover letter assistant AI.

Given the following resume and job description, write a tailored, professional, and enthusiastic cover letter that highlights the candidate’s strengths and matches the job requirements.

Resume:
{resume_text}

Job Description:
{job_text}

Please write the full cover letter below:
"""
    result = None # Default value

    # To check API key exists
    api_key = os.getenv("HF_API_key")
    if not api_key:
        raise ValueError("API key not found in environment variables!")


    # Prepare headers and payload
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs" : prompt,
        "parameters" : {
            "temperature" : 0.7,
            "top_p" : 0.9,
            "max_new_tokens" : 500,
            "do_sample" : True,
            "repetition_penalty": 1.2
        }
    }

    try:
        # Send the request to API
        response = requests.post("",headers=headers,json=payload,timeout=30)
        response.raise_for_status()    ## Raise error if response code is not 200
        result = response.json()
        return result[0]["generated_text"].strip()
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out. Try again later.")
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
            job_text = escape(request.form.get("job_description",'').strip())

            if resume_file.filename == '':
                abort(400,"No selected file")
            if not allowed_file(resume_file.filename):
                abort(400,"Only PDF files are allowed")
            if len(job_text) < 20:
                abort(400,"Job description is too short (min 20 characters)")

            # Process in memory without saving
            resume_text = extract_txt(resume_file.stream)
            cover_letter = generate_cover_letter(resume_text, job_text)
            return render_template("index.html", result = cover_letter)

        except ValueError as e:
            abort(400,str(e))
        except RuntimeError as e:
            abort(503,str(e))
        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            abort(500, "Internal server error")

    return render_template("index.html", result = None)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
