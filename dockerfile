FROM python:3.9-slim
RUN apt-get update && apt-get install -y tesseract-ocr
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY bot.py .
CMD ["python", "bot.py"]
