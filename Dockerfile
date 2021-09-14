FROM python:3.8

COPY ./final /app
WORKDIR /app

RUN apt-get update && apt-get install -y cmake libgl1-mesa-glx libgl1-mesa-dev

# COPY requirements.txt .
RUN pip install -r requirements.txt

CMD ["python3", "essential.py"]