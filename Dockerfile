# 国内镜像加速（可按需改成 docker.m.daocloud.io / docker.xuanyuan.me）
ARG REGISTRY=docker.1ms.run

FROM ${REGISTRY}/library/docker:27-cli AS dockercli

FROM ${REGISTRY}/library/python:3.12-slim

WORKDIR /app

COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY app ./app

RUN mkdir -p uploads

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
