FROM docker.arvancloud.ir/library/python:3.12-slim

USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    wget \
    software-properties-common \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/jupyter

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Create directories for data and notebooks
RUN mkdir -p /opt/jupyter/data /opt/jupyter/notebooks /opt/jupyter/src /opt/jupyter/scripts

# Expose Jupyter port
EXPOSE 8888

# Default command to start Jupyter
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=''", "--NotebookApp.password=''"] 