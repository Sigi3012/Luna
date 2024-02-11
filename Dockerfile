FROM python:3.11.6-slim

WORKDIR /bot

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY persistent/ persistent/

COPY . .

CMD [ "python", "-u", "main.py" ]
