from flask import Flask, render_template, request, abort, redirect, url_for, flash
import pdfplumber
import google.generativeai as genai
import os
import re

# ───────────────────────────────────────
#  Flask App Configuration
# ───────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 7 * 1024 * 1024  # Restrict file uploads to max 7MB
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}          # Only allow PDF uploads
app.secret_key = os.urandom(24)                    

# ───────────────────────────────────────
#  File Format Check
# ───────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ───────────────────────────────────────
#  Extract Text From PDF
# ───────────────────────────────────────
def extract_txt(pdf_file):
    """Extracts all readable text from a PDF using pdfplumber"""
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
        raise RuntimeError(f" Failed to extract text: {str(e)}")

# ───────────────────────────────────────
#  Validate & Build Contact Block
# ───────────────────────────────────────
def build_clean_contact_block(email, phone, github, linkedin):
    contact = ""
    warnings = []

    #  Check Email
    if email:
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            contact += email
        else:
            warnings.append(" Invalid email format.")

    #  Check Phone (we expect country code + 10 digits = 13 chars)
    if phone:
        digits = re.sub(r"(?!^\+)\D", "", phone)
        if len(digits) == 13:
            contact += (" | " if contact else "") + digits
        else:
            warnings.append(" Phone must be 10 digits (e.g., 9876543210).")

    #  Check GitHub URL
    if github:
        if re.match(r"^https?://(www\.)?github\.com/[\w-]+/?$", github.strip()):
            contact += f"\nGitHub: {github.strip()}"
        else:
            warnings.append(" Invalid GitHub URL.")

    #  Check LinkedIn URL
    if linkedin:
        if re.match(r"^https?://(www\.)?linkedin\.com/in/[\w-]+/?$", linkedin.strip()):
            contact += f" | LinkedIn: {linkedin.strip()}"
        else:
            warnings.append(" Invalid LinkedIn URL.")

    return contact, warnings

# ───────────────────────────────────────
#  Generating Cover Letter with Gemini
# ───────────────────────────────────────
def generate_cover_letter(resume_text, job_text, contact_block):
    if not resume_text or not job_text:
        raise ValueError("Missing input!")

    #  Prompt to guide Gemini
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

    #  Load Gemini API key
    apikey = os.environ.get("GOOGLE_API_KEY")
    if not apikey:
        raise ValueError("API key not found!")

    genai.configure(api_key=apikey)

    try:
        model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")
        response = model.generate_content(prompt)
        print(" Raw Gemini Response Object:", response)

        try:
            result = response.text.strip()
            print(" Gemini Response Text:", result)
            return result
        except Exception as e:
            print(" Could not extract .text from response:", str(e))
            return " Gemini returned an unrecognized format."

    except Exception as e:
        raise RuntimeError(f"Gemini API Error: {str(e)}")

#   Route: Home Page (GET/POST)
# ───────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            #  Collect form inputs
            form_data = {
                "email": request.form.get("email", "").strip(),
                "phone": request.form.get("phone", "").strip(),
                "github": request.form.get("github", "").strip(),
                "linkedin": request.form.get("linkedin", "").strip(),
                "job_description": request.form.get("job_description", "").strip(),
                "country_code": request.form.get("country_code", "+91")
            }

            #  Check if resume is uploaded
            if "resume" not in request.files:
                abort(400, "No resume uploaded")

            resume_file = request.files["resume"]
            job_text = form_data["job_description"]

            #  Validate contact info
            full_phone = f'{form_data["country_code"]} {form_data["phone"]}'
            contact_block, warnings = build_clean_contact_block(
                form_data["email"], full_phone, form_data["github"], form_data["linkedin"]
            )

            #  Show warnings (e.g. bad email)
            if warnings:
                for msg in warnings:
                    flash(msg, "warning")
                return render_template("index.html", form_data=form_data, result=None)

            #  File checks
            if resume_file.filename == '':
                abort(400, "No file selected")
            if not allowed_file(resume_file.filename):
                abort(400, "Only PDF files are accepted")
            if len(job_text) < 20:
                flash(" Job description must be at least 20 characters.", "danger")
                return render_template("index.html", form_data=form_data, result=None)

            #  Extract resume text + generate letter
            resume_text = extract_txt(resume_file.stream)
            print(" Resume Text:", resume_text[:1000])
            print(" Job Description:", job_text[:1000])

            cover_letter = generate_cover_letter(resume_text, job_text, contact_block)
            return render_template("index.html", result=cover_letter, form_data=form_data)

        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            abort(500, "Internal Server Error")

    # First visit (or GET)
    return render_template("index.html", result=None, form_data={})

# Run the Flask App 
# ───────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 7860)))
