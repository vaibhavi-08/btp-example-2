FROM python:3.11-slim

WORKDIR /project

COPY . .

CMD ["python", "app/main.py"]