FROM ubuntu:20.04

RUN apt-get update
RUN apt-get -y install python3-pip git-core

RUN mkdir /opt/api
RUN mkdir /opt/api/program
WORKDIR /opt/api/program/
COPY . /opt/api/program/
RUN pip3 install -r requirements.txt
EXPOSE 8181
RUN ls /opt/api/program/

CMD ["uvicorn", "master-api:app", "--host", "0.0.0.0", "--port", "8181"]
