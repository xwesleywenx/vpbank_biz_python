FROM python:3.12-alpine as base

FROM base as builder

# 指定 Image 中的工作目錄
WORKDIR /docker

# 將 Dockerfile 所在目錄下的所有檔案複製到 Image 的工作目錄 /code 底下
ADD . /docker

# 在 Image 中執行的指令：安裝 requirements.txt 中所指定的 dependencies
RUN pip install -r requirements.txt

# Expose port 23120 to the outside world
EXPOSE 23120

CMD [ "python", "app.py" ]