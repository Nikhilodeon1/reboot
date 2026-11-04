FROM python:3.11-slim
RUN pip install --no-cache-dir numpy pyarrow polars && pip freeze > /pip_freeze.txt
WORKDIR /work
