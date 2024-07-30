# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim

#ENV HOST=0.0.0.0
#ENV LISTEN_PORT 8000
EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Use an official Python runtime as a parent image
# Set the working directory
WORKDIR /app


# Install essential packages and clean up to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential \
    curl \
    apt-utils \
    gnupg2 &&\
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip

# Re-update apt packages after cleaning up in the previous step
RUN apt-get update

# Add the Microsoft repository GPG keys to the list of trusted keys
#RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/keys/microsoft.asc |  tee /etc/apt/trusted.gpg.d/microsoft.asc

# Add the Microsoft package repository to the system
#RUN curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list 
RUN curl https://packages.microsoft.com/config/debian/11/prod.list |  tee /etc/apt/sources.list.d/mssql-release.list

# Dummy command to ensure previous RUN commands succeed before proceeding
RUN exit

# Update apt-get with new sources from Microsoft
RUN apt-get update

# Install the Microsoft ODBC SQL Driver 18
RUN env ACCEPT_EULA=Y apt-get install -y msodbcsql18 


# Copy the current directory contents into the container at /app
# Copy the requirements file into the container at /app
COPY requirements.txt .

# Copy the ODBC configuration file into the container at the root directory
COPY /odbc.ini / 

# Register the SQL Server data source name specified in odbc.ini
RUN odbcinst -i -s -f /odbc.ini -l

# Display the contents of the ODBC configuration file to verify correct setup
RUN cat /etc/odbc.ini

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py chainlit.md ./
COPY assistant_flow/*  ./assistant_flow/
COPY survey_data_insights/*  ./survey_data_insights/
COPY .chainlit ./.chainlit

RUN ls -la
# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
#RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
#USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
#CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port",  "8000"]

CMD ["python", "app.py", "--host", "0.0.0.0", "--port",  "8000"]
