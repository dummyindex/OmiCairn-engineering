FROM ubuntu:22.04

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN echo no | dpkg-reconfigure dash

ARG TZ=UTC
ENV TZ=${TZ}
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && \
    apt-get install -y curl && \
    apt-get install -y jq && \
    apt-get install -y make && \
    apt-get install -y libpq-dev && \
    apt-get install -y build-essential libxml2-dev python3-dev python3-pip zlib1g-dev python3-requests python3-aiohttp python3-venv python3-tk

WORKDIR /omicairn_root

COPY requirements.txt requirements.txt

# Optional: override the Python package index at build time, e.g.
#   docker build --build-arg PIP_INDEX_URL=https://my.mirror/simple .
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN pip3 install --index-url ${PIP_INDEX_URL} -r requirements.txt

COPY . .

# Cloud credentials and service configuration are supplied at runtime via
# environment variables (see .env.example), never baked into the image.
ENTRYPOINT ["bash","./omicairn_scripts/omicairn_docker_container_entrypoint.sh"]

EXPOSE 80
