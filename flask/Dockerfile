FROM python:latest

WORKDIR /usr/src/app

COPY ./requirements.txt ./

RUN pip install --no-cache-dir -r ./requirements.txt

COPY ./SCIM ./SCIM
COPY ./run.py ./run.py

CMD ["gunicorn", "-b", "0.0.0.0:5001", "--workers=2", "--threads=4", "--worker-class=gthread", "--log-file=-", "run:app"]
EXPOSE 5001