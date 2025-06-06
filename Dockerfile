FROM python:3.9-alpine

WORKDIR /

COPY requirements.txt . 
RUN pip install -r requirements.txt

COPY ./database /database
COPY ./scripts /scripts
COPY ./pipeline /pipeline
COPY ./tests /tests
COPY .env /

ENV PYTHONPATH="/:${PYTHONPATH}"


