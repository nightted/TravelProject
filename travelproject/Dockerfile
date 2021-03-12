FROM python:3.8.6
LABEL maintainer twtrubiks
ENV PYTHONUNBUFFERED 1
RUN mkdir /travelproject
WORKDIR /travelproject
COPY . /travelproject/
RUN pip install -r requirements.txt
