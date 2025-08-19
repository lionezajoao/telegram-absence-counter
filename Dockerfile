FROM python:3.12-alpine

WORKDIR /usr/src/app

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    postgresql-dev \
    wget

COPY Pipfile Pipfile.lock ./

# Install project dependencies
RUN pip install pipenv && \
    pipenv requirements > requirements.txt && \
    pip install -r requirements.txt

# Clean up build dependencies
RUN apk del .build-deps

COPY . .

CMD ["sh", "-c", "alembic upgrade head && python -m app.main"]
