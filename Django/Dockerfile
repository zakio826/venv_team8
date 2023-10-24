FROM python:3.11
WORKDIR /code
ADD requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
