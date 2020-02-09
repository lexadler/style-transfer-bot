FROM python:3.8-buster
ENV PYTHONPATH "${PYTHONPATH}:/app"
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel 
RUN pip install -r requirements.txt
COPY *.py /app/
ENTRYPOINT ["python"]
CMD ["run.py"]
