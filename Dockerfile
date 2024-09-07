FROM python:3.11.9-bookworm
WORKDIR /app
COPY . .
RUN apt-get -y update
RUN apt-get install -y ffmpeg
RUN pip install -r ./requirements.txt
CMD ["python3","main.py"]
