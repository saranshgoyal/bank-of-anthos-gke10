# Use the official Python docker container, slim version, running Debian
FROM python:3.12.6-slim@sha256:ad48727987b259854d52241fac3bc633574364867b8e20aec305e6e7f4028b26 as base
WORKDIR /app
FROM base as builder

# Install dependencies.
COPY requirements.txt .
RUN pip install --prefix="/install" -r requirements.txt

FROM base

RUN adduser --disabled-password --gecos "" myuser && \
    chown -R myuser:myuser /app

# Set our working directory


COPY --from=builder /install /usr/local

# show python logs as they occur
ENV PYTHONUNBUFFERED=0

# explicitly set a fallback log level in case no log level is defined by Kubernetes
ENV LOG_LEVEL info

# Add application code.
COPY . .

USER myuser

ENV PATH="/home/myuser/.local/bin:$PATH"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
