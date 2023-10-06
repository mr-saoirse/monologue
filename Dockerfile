FROM python:3.10-slim as base

RUN apt update && apt install -y curl gpg
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg;
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null;
RUN apt install -y git gh
RUN pip install -U pip poetry

WORKDIR /app

COPY pyproject.toml ./
RUN poetry install --no-dev --no-root --no-interaction --no-ansi

COPY ./monologue /app/monologue
COPY ./README.md /app/README.md
RUN poetry build
RUN poetry install

ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PYTHONUNBUFFERED=0

ENTRYPOINT [ "poetry", "run", "monologue", "test"  ]
#docker build --platform linux/amd64 -t monologue:latest . 
#docker run  --platform linux/amd64 -t monologue

#https://github.com/pola-rs/polars/issues/540