# ubuntu docker python
FROM gradle:jdk21

ENV PATH="${PATH}:/app/gradle-8.5/bin"
RUN gradle --version
# RUN echo "org.gradle.jvmargs=-Xm2048m" > /home/gradle/.gradle/gradle.properties
RUN echo "org.gradle.daemon=false" >> /home/gradle/.gradle/gradle.properties
RUN echo "org.gradle.parallel=true" >> /home/gradle/.gradle/gradle.properties

# Install Maven
RUN apt-get update && \
    apt-get install -y maven && \
    rm -rf /var/lib/apt/lists/*

# Verify Maven installation
RUN mvn --version

### prepare templates
WORKDIR /app
COPY templates /app/templates

# Prepare the Java 8 environment
WORKDIR /app/templates/java8/spring-boot-payroll-example
RUN gradle build
# remove the folder
WORKDIR /app/templates/java8
RUN rm -rf spring-boot-payroll-example
# Prepare the Java 21 environment
WORKDIR /app/templates/java21/spring-boot-payroll-example
RUN gradle build
# remove the folder
WORKDIR /app/templates/java21
RUN rm -rf spring-boot-payroll-example

### Install python and pip
WORKDIR /app
RUN apt-get update \
    && apt-get install -y python3.11 python3-pip python3.11-venv
# Create and activate virtual environment (needed since debian 12)
RUN python3.11 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --upgrade pip 
RUN pip install --upgrade setuptools
COPY tools/ ./tools
COPY requirements.txt .
RUN pip install -r requirements.txt

### Copy repo and start
COPY src/code_executor/ ./src/code_executor
ENV PYTHONPATH=.
ENV ENABLE_OTEL_LOG_HANDLER="true"
COPY config.yaml .

# Define the entry point for the container
CMD ["python", "src/code_executor/main.py"]