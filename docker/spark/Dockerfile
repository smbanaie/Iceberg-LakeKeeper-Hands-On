FROM docker.arvancloud.ir/bitnami/spark:3.5.2

USER root

# Set Spark home
ENV SPARK_HOME=/opt/bitnami/spark

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    wget \
    python3-pip \
    python3-setuptools \
    python3-dev \
    build-essential \
    software-properties-common \
    ssh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.10.9.5-src.zip:$PYTHONPATH
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Download Iceberg Spark runtime
RUN wget https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.9.1/iceberg-spark-runtime-3.5_2.12-1.9.1.jar -P $SPARK_HOME/jars/

# Download AWS S3 dependencies
RUN wget https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.31.9/bundle-2.31.9.jar  -P $SPARK_HOME/jars/ && \
    wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.1/hadoop-aws-3.4.1.jar  -P $SPARK_HOME/jars/ && \
    wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.787/aws-java-sdk-bundle-1.12.787.jar -P $SPARK_HOME/jars/

# Download PostgreSQL JDBC driver
RUN wget https://jdbc.postgresql.org/download/postgresql-42.7.7.jar -P $SPARK_HOME/jars/

# Create directories for data and notebooks
RUN mkdir -p $SPARK_HOME/data $SPARK_HOME/notebooks $SPARK_HOME/src $SPARK_HOME/scripts

# Copy Spark configuration
COPY conf/spark-defaults.conf $SPARK_HOME/conf/

# Set working directory
WORKDIR $SPARK_HOME

# Expose ports for Spark UI and Jupyter
EXPOSE 4040 8080 8081 8888

# Default command
CMD ["bin/spark-class", "org.apache.spark.deploy.master.Master"]
