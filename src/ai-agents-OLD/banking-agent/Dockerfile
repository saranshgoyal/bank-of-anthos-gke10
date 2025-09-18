# Use the official Python docker container, slim version, running Debian
FROM python:3.12.6-slim@sha256:ad48727987b259854d52241fac3bc633574364867b8e20aec305e6e7f4028b26 as base

FROM base as builder

# Install dependencies.
COPY requirements.txt .
RUN pip install --prefix="/install" -r requirements.txt

FROM base

# Set our working directory
WORKDIR /app

COPY --from=builder /install /usr/local

# show python logs as they occur
ENV PYTHONUNBUFFERED=0

# explicitly set a fallback log level in case no log level is defined by Kubernetes
ENV LOG_LEVEL info

# Add application code.
COPY . .

# Ensure files are readable for non-root users
RUN chmod a+r *

# Start server using gunicorn
# CMD gunicorn -b :$PORT --threads 2 --log-config logging.conf --log-level=$LOG_LEVEL "userservice:create_app()"
# CMD ["adk", "api_server", "./banking-agent.py"]
# CMD ["adk", "api_server", "--port",  "8080"]

CMD ["adk", "web"]
