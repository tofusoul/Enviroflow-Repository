
FROM python:3.10

# System dependencies (if needed)
RUN apt-get update && apt-get install -y \
	build-essential \
	&& rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy project files
COPY . /app

# Install Poetry
RUN pip install --upgrade pip \
	&& pip install poetry

# Configure Poetry
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VENV_IN_PROJECT=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

# Install dependencies using Poetry
RUN poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR

# Activate the virtual environment by updating PATH
ENV PATH="/app/.venv/bin:$PATH"

# Add Python packages to PATH
ENV PATH="/root/.local/bin:$PATH"

# Expose Streamlit default port
EXPOSE 8501

# Entrypoint to run the Streamlit app
CMD ["python", "-m", "streamlit", "run", "enviroflow_app/🏠_Home.py", "--server.address=0.0.0.0"]
