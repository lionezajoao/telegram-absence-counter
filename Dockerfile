FROM python:alpine

WORKDIR /usr/src/app

RUN pip install pipenv

COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy
RUN pipenv install python-docx

COPY . .

CMD ["pipenv", "run", "bot"]