FROM python:3.13-slim as production

ENV PYTHONUNBUFFERD=1
WORKDIR /app/

COPY requirements/prod.txt ./requirements/prod.txt
RUN pip install -r ./requirements/prod.txt

COPY manage.py ./manage.py
COPY setup.cfg ./setup.cfg
COPY mysite ./mysite

EXPOSE 8000