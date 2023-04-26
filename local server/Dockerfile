FROM python:3.10

ADD local_server.py .
ADD station.py .

RUN pip install paho-mqtt
CMD ["python", "./local_server.py"]
