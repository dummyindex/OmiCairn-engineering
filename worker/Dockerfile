FROM ubuntu:22.04

WORKDIR /omicairn

WORKDIR /omicairn/store

WORKDIR /omicairn/code_space

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN echo no | dpkg-reconfigure dash

RUN bash

ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && \
    apt-get install -y curl && \
    apt-get install -y jq && \
    apt-get install -y make && \
    apt-get install -y libpq-dev && \
    apt-get install -y build-essential libxml2-dev python3-dev python3-pip zlib1g-dev python3-requests python3-aiohttp python3-venv python3-tk
RUN apt-get install -y gfortran
RUN apt-get install -y libopenblas-dev liblapack-dev libatlas-base-dev

COPY requirements-server.txt /omicairn/code_space/requirements-server.txt

RUN pip3 install -r /omicairn/code_space/requirements-server.txt

RUN apt-get update && apt-get install -y \
    ca-certificates \
    gnupg \
    lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y software-properties-common dirmngr gnupg apt-transport-https ca-certificates && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 51716619E084DAB9 && \
    add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu jammy-cran40/' && \
    apt-get update && apt-get install -y r-base r-base-dev

RUN python3 -m venv /omicairn/venvs/file_resolver_env

COPY file_resolver /omicairn/code_space/file_resolver

RUN /omicairn/venvs/file_resolver_env/bin/pip install -r /omicairn/code_space/file_resolver/requirements.txt

WORKDIR /omicairn/code_space

COPY . .

WORKDIR /

ENTRYPOINT [ "bash", "/omicairn/code_space/scripts/launch.sh" ]

EXPOSE 80
