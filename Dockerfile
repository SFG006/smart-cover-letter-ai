# Use a lightweight official Python image
FROM python:3.10-slim

# Set working directory in the container
WORKDIR /app

# Copy project files into the container
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port 7860 (used by Hugging Face Spaces)
EXPOSE 7860

# Start Flask app using Gunicorn (production-grade server)
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]