# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed Python packages specified in requirements.txt
# (Assuming you have a requirements.txt file with all dependencies listed)
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 to the outside world
EXPOSE 8080

# Run the Twilio WhatsApp LLM integration script when the container launches
CMD ["python", "twilio_whatsapp_llm_integration.py"]
