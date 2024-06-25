FROM python:3.12.4-bullseye

ENV POETRY_VERSION=1.7.1 POETRY_HOME=/poetry
ENV PATH=/poetry/bin:$PATH
RUN curl -sSL https://install.python-poetry.org | python3 -
WORKDIR /d3fau1t/audiate
COPY pyproject.toml poetry.lock README.md ./
RUN apt update -y && apt install portaudio19-dev flac ffmpeg -y
RUN poetry install --only main --no-interaction --no-ansi
COPY app app
COPY sounds sounds
COPY tests tests
COPY bin/start /bin/start
CMD ["/bin/start"]
