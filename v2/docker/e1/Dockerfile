FROM python:3.11-slim
RUN pip install --no-cache-dir "pandas<2.2" "numpy<2" "great-expectations>=0.18,<0.19" pandera fairlearn aif360 scikit-learn \
    && pip freeze > /pip_freeze.txt
WORKDIR /work
