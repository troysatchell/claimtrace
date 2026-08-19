# claimtrace demo — CPU container (Railway / Render / HF Docker Space).
# Two Qwen3-1.7B models in bf16 need ~8 GB RAM; give the service >= 10 GB.
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 HF_HOME=/data/hf PORT=7860 GRADIO_SERVER_NAME=0.0.0.0
WORKDIR /app
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir "transformers>=4.51" accelerate safetensors "gradio>=4.44"
COPY app.py ledger.py ./
EXPOSE 7860
CMD ["python", "app.py"]
