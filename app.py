from flask import Flask, render_template , request , abort , redirect, url_for, session , flash
from werkzeug.utils import secure_filename
import pdfplumber
import requests
import os
from dotenv import load_dotenv
import  re


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

#  Validate and Clean the Contact Inputs Before Displaying
def build_clean_contact_block(email, phone, github, linkedin):
    contact = ""
    warnings = []

    # ✅ Email validation
    if email:
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            contact += email
        else:
            warnings.append("⚠ Invalid email format.")

    # ✅ Phone validation: 10 digits, digits only
    if phone:
        digits = re.sub(r"(?!^\+)\D", "", phone)
        if len(digits) == 13:
            if contact:
                contact += " | "
            contact += f"{digits}"
        else:
            warnings.append("⚠ Phone must be 10 digits (e.g., 9876543210).")

    # ✅ GitHub URL validation
    if github:
        if re.match(r"^https?://(www\.)?github\.com/[\w-]+/?$", github.strip()):
            contact += f"\nGitHub: {github.strip()}"
        else:
            warnings.append("⚠ Invalid GitHub URL. Use format: https://github.com/username")

    # ✅ LinkedIn URL validation
    if linkedin:
        if re.match(r"^https?://(www\.)?linkedin\.com/in/[\w-]+/?$", linkedin.strip()):
            contact += f" | LinkedIn: {linkedin.strip()}"
        else:
            warnings.append("⚠ Invalid LinkedIn URL. Use format: https://www.linkedin.com/in/username")

    return contact, warnings


# Generate Cover Letter
def generate_cover_letter(resume_text, job_text, contact_block):
    """Generate cover letter with robust API handling"""
    if not resume_text and not job_text:
        raise ValueError("Missing required input")
    # Prepare the prompt
    prompt = f"""You are a professional cover letter writing assistant AI.

    Your task is to write a fully personalized and professional cover letter using the resume and job description provided below. The tone should be confident, enthusiastic, and natural — similar to a human writing style. Do not include any placeholders or incomplete information.

    ---

    Start the letter with this full name, extracted from the resume: [Extracted Name from resume_text]  
    Then include this contact block exactly as provided — do not modify or override it with content from the resume:

    {contact_block}

    ---

    Resume:
    {resume_text}

    ---

    Job Description:
    {job_text}

    ---

    Instructions for the Cover Letter:
    - Start the letter with this full name, extracted from the resume {resume_text}: [Extracted Name from resume_text]  
    - Then include this contact block {contact_block} exactly as provided — do not modify or override it with content from the resume:
    - If the company name is provided, use it exactly. If not, leave it as “[Company Name]” — do not invent a new one.
    - Use this subject line format: **Application for [Job Title] Position** — where the job title is inferred from the job description.
    - Start with a warm, enthusiastic introduction mentioning the job role and why the applicant is interested.
    - Highlight 1–2 relevant achievements, certifications, or projects that match the job requirements.
    - Emphasize relevant technical skills such as cloud platforms (AWS, Azure, GCP), scripting (Python, Bash), Kubernetes, Docker, Terraform, etc., based on the resume.
    - Briefly mention soft skills or extracurriculars (e.g., mentoring, communication, creative projects) that show cultural fit.
    - Include a short paragraph about why the applicant is excited to work at the company named in the job description.
    - End with a confident call to action and close with this format:

    Sincerely,  
    [Extracted Name from resume_text]

    ---

    Return only the complete cover letter in plain text. Do not include markdown formatting, brackets, or any extra symbols.
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
            # Always store form data early
            form_data = {
                "email": request.form.get("email", "").strip(),
                "phone": request.form.get("phone", "").strip(),
                "github": request.form.get("github", "").strip(),
                "linkedin": request.form.get("linkedin", "").strip(),
                "job_description": request.form.get("job_description", "").strip(),
                "country_code": request.form.get("country_code", "+91")

            }
            session["form_data"] = form_data

            if "resume" not in request.files:
                abort(400,"No resume file uploaded")

            resume_file = request.files["resume"]
            job_text = form_data["job_description"]

            full_phone = f'{form_data["country_code"]} {form_data["phone"]}'
            contact_block, warnings = build_clean_contact_block(
                form_data["email"],
                full_phone,
                form_data["github"],
                form_data["linkedin"]
            )

            # Show any contact warnings
            if warnings:
                for w in warnings:
                    flash(w, "warning")
                return redirect(url_for("index"))   # Don't proceed to generate the cover letter



            if resume_file.filename == '':
                abort(400, "No selected file")
            if not allowed_file(resume_file.filename):
                abort(400, "Only PDF files are allowed")
            if len(job_text) < 20:
                flash("❗ Job description must be at least 20 characters long.", "danger")
                return redirect(url_for("index"))

            resume_text = extract_txt(resume_file.stream)
            cover_letter = generate_cover_letter(resume_text, job_text, contact_block)
            session["cover_letter"] = cover_letter
            session.pop("form_data", None)  # clean after success
            return redirect(url_for("index"))

        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            abort(500, "Internal server error")

    cover_letter = session.pop("cover_letter", None)
    form_data = session.pop("form_data", {})  # stay safe
    return render_template("index.html", result=cover_letter, form_data=form_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 7860)))


