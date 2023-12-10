FROM python:3.10

WORKDIR /carbon_app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["python", "app.py"]
