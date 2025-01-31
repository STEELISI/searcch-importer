FROM ubuntu:20.04

RUN apt-get update -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip sqlite3 git libgit2-dev \
        ca-certificates iproute2 nano libxml2-dev libxslt1-dev zlib1g-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /searcch-importer

COPY requirements.txt /searcch-importer

RUN pip3 install -r requirements.txt

COPY scripts/fetch-corpora.sh /searcch-importer/scripts/

COPY scripts/import-and-publish /searcch-importer/import-and-publish

RUN sh scripts/fetch-corpora.sh

COPY setup.py setup.cfg gunicorn_wrapper.py /searcch-importer/
COPY src /searcch-importer/src

RUN python3 setup.py install

CMD [ "/bin/bash" ]
