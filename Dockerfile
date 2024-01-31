# stage 1: build
FROM python:3.11-slim-buster AS builder

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update && \
    apt-get install -y git && \
    python3 -m pip install --upgrade pip

WORKDIR /app

COPY .git/ ./.git/
COPY ./requirements.txt .

RUN pip install -r requirements.txt 
RUN apt-get clean

# stage 2: run the flask app
FROM python:3.11-slim-buster

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY ./kairos ./kairos
COPY ./app.py .

EXPOSE 5000
CMD ["gunicorn", "--workers=3", "--threads=3", "-b", ":5000", "app:app", "--timeout 1000"]