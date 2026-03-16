FROM python:3.11

WORKDIR /app

COPY . /app

RUN pip install flask flask-mail authlib python-dotenv requests flask-wtf

EXPOSE 5000

CMD ["python", "app.py"]