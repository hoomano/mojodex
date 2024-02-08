# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY app /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Run your Python script
CMD ["python", "main.py"]