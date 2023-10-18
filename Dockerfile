# Use an official Python runtime as a base image
FROM python:3.10.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY requirement.txt /app/requirement.txt
# Install necessary dependencies
RUN pip install -r requirement.txt

COPY . /app

# Expose the port that the app will run on
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "app.py"]
