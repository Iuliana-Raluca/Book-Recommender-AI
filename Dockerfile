FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY .gradio/ .gradio/
COPY db/ db/
COPY src/data/ src/data/

EXPOSE 7860

CMD ["python", "src/app.py"]
