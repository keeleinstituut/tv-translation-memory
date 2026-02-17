# syntax = docker/dockerfile:1.4.0

FROM docker.io/bitnamilegacy/spark:3.4 as spark

FROM node:latest as node

COPY src/RestApi /app/src/RestApi
RUN npm install apidoc -g

WORKDIR /app/src/RestApi
RUN apidoc -i . -o ../../doc_build

FROM python:3.11-bullseye

ENV SPARK_HOME /opt/bitnami/spark
COPY --from=spark $SPARK_HOME $SPARK_HOME

ARG TARGETARCH
ENV DEBIAN_FRONTEND noninteractive
ENV ELASTICTM /opt/elastictm
ENV ELASTICTM_VOLUME /elastictm
ENV GUNICORN_WORKERS 4
ENV ENTRYPOINT /entrypoint.sh
VOLUME $ELASTICTM_VOLUME

# Copy only doc_build from node stage
COPY --from=node /app/doc_build $ELASTICTM/doc_build

## LEGACY: The volume at /elastictm and the logs contained in it appear to never get used/modified.
#RUN mkdir -p $ELASTICTM_VOLUME/log/elastictm && \
#    touch $ELASTICTM_VOLUME/log/elastictm/gunicorn.log $ELASTICTM_VOLUME/log/elastictm/celery-worker.log && \
#    chmod -R oag+w $ELASTICTM_VOLUME/log/elastictm
## LEGACY: Due to the log files remaining empty, Logrotate will be passive in the container.
#RUN ln -s conf/logrotate.conf /etc/logrotate.d/activatm

# Install runtime dependencies and build dependencies (build deps will be removed later)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libboost-all-dev \
      libtercpp-dev \
      default-jdk \
      default-jre \
      iputils-ping \
      libatlas-base-dev \
      libblas-dev \
      libcurl4-openssl-dev \
      liblapack-dev \
      libssl-dev \
      libxml2-dev \
      libxslt1-dev \
      supervisor \
      zip \
      ruby \
      # Build dependencies (will be removed after compilation)
      build-essential \
      gfortran \
      git \
      swig \
      wget \
      curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY src/ $ELASTICTM/src/
COPY tools/ $ELASTICTM/tools/
COPY conf/ $ELASTICTM/conf/
COPY requirements.txt $ELASTICTM/

WORKDIR $ELASTICTM

# Extract TreeTagger parameter files
WORKDIR $ELASTICTM/tools/tree-tagger-linux-3.2
RUN mkdir -p lib && \
    if [ -f english-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd english-par-linux-3.2-utf8.bin.gz > lib/english-utf8.par && \
        ln -s english-utf8.par lib/english.par; \
    fi && \
    if [ -f french-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd french-par-linux-3.2-utf8.bin.gz > lib/french-utf8.par && \
        ln -s french-utf8.par lib/french.par; \
    fi && \
    if [ -f spanish-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd spanish-par-linux-3.2-utf8.bin.gz > lib/spanish-utf8.par && \
        ln -s spanish-utf8.par lib/spanish.par; \
    fi && \
    if [ -f italian-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd italian-par-linux-3.2-utf8.bin.gz > lib/italian-utf8.par && \
        ln -s italian-utf8.par lib/italian.par; \
    fi && \
    if [ -f german-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd german-par-linux-3.2-utf8.bin.gz > lib/german-utf8.par && \
        ln -s german-utf8.par lib/german.par; \
    fi && \
    if [ -f slovak-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd slovak-par-linux-3.2-utf8.bin.gz > lib/slovak-utf8.par && \
        ln -s slovak-utf8.par lib/slovak.par; \
    fi && \
    if [ -f dutch-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd dutch-par-linux-3.2-utf8.bin.gz > lib/dutch-utf8.par && \
        ln -s dutch-utf8.par lib/dutch.par; \
    fi && \
    if [ -f portuguese-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd portuguese-par-linux-3.2-utf8.bin.gz > lib/portuguese-utf8.par && \
        ln -s portuguese-utf8.par lib/portuguese.par; \
    fi && \
    if [ -f romanian-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd romanian-par-linux-3.2-utf8.bin.gz > lib/romanian-utf8.par && \
        ln -s romanian-utf8.par lib/romanian.par; \
    fi && \
    if [ -f bulgarian-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd bulgarian-par-linux-3.2-utf8.bin.gz > lib/bulgarian-utf8.par && \
        ln -s bulgarian-utf8.par lib/bulgarian.par; \
    fi && \
    if [ -f polish-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd polish-par-linux-3.2-utf8.bin.gz > lib/polish-utf8.par && \
        ln -s polish-utf8.par lib/polish.par; \
    fi && \
    if [ -f estonian-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd estonian-par-linux-3.2-utf8.bin.gz > lib/estonian-utf8.par && \
        ln -s estonian-utf8.par lib/estonian.par; \
    fi && \
    if [ -f finnish-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd finnish-par-linux-3.2-utf8.bin.gz > lib/finnish-utf8.par && \
        ln -s finnish-utf8.par lib/finnish.par; \
    fi && \
    if [ -f russian-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd russian-par-linux-3.2-utf8.bin.gz > lib/russian-utf8.par && \
        ln -s russian-utf8.par lib/russian.par; \
    fi && \
    if [ -f slovenian-par-linux-3.2-utf8.bin.gz ]; then \
        gzip -cd slovenian-par-linux-3.2-utf8.bin.gz > lib/slovenian-utf8.par && \
        ln -s slovenian-utf8.par lib/slovenian.par; \
    fi && \
    chmod -R o+rX lib/

WORKDIR $ELASTICTM

WORKDIR /tmp
COPY ./tools/kytea/kytea-0.4.7.tar.gz .
RUN tar -xzf kytea-0.4.7.tar.gz && \
    cd kytea-0.4.7 && \
    if [ "$TARGETARCH" = "arm64" ] || [ "$TARGETARCH" = "arm32" ]; \
        then ./configure --build=aarch64-unknown-linux-gnu; \
        else ./configure; \
    fi && \
    make && \
    make install && \
    ldconfig && \
    cd .. && \
    rm -rf kytea-0.4.7 kytea-0.4.7.tar.gz

WORKDIR $ELASTICTM

# Upgrade pip to the latest version
RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# Build and install Mykytea-python from source as fallback
# The pip package may not work correctly or may not provide Mykytea module
# Using v0.1.9 tag to match the requirements.txt version
WORKDIR /tmp/Mykytea-python
RUN git clone https://github.com/chezou/Mykytea-python.git . && \
    git checkout v0.1.9 && \
    make && \
    make install && \
    cd .. && \
    rm -rf Mykytea-python

WORKDIR $ELASTICTM/tools/pytercpp
RUN git clone https://github.com/cservan/tercpp.git && \
    git -C tercpp checkout cef1e60 && \
    python setup.py build install && \
    rm -rf tercpp

WORKDIR $ELASTICTM

# Download universal POS tagset
# Note: NLTK 3.9+ uses punkt_tab in addition to punkt for sentence tokenization
RUN python -m nltk.downloader -d /usr/share/nltk_data universal_tagset stopwords punkt punkt_tab

COPY tools/universal-pos-tags-master/*-treetagger-pg.map /usr/share/nltk_data/taggers/universal_tagset/

RUN apt-get purge -y \
      build-essential \
      gfortran \
      git \
      swig \
      wget \
      curl && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN chown -R root:root ${ELASTICTM} && \
    chmod -R o+rX ${ELASTICTM}

RUN mkdir -p /tmp/elastictm/export && \
    chown -R www-data:www-data /tmp/elastictm/export && \
    chmod 755 /tmp/elastictm/export

RUN chmod -R o+rX $SPARK_HOME

RUN chmod -R o+rX /usr/share/nltk_data

RUN sed -i 's/^\(\[supervisord\]\)$/\1\nnodaemon=true/' /etc/supervisor/supervisord.conf

RUN <<EOF cat > /etc/supervisor/conf.d/supervisor.conf
[program:gunicorn]
user=www-data
environment=HOME="/home/www-data",USER="www-data"
process_name=%(program_name)s
numprocs=1
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes = 0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
directory=$ELASTICTM/src
command=gunicorn
          -m 007
          --bind 0.0.0.0:8000
          --workers $GUNICORN_WORKERS
          --capture-output
          --log-level INFO
          --access-logfile '-'
          RestApi.Api:app

[program:celery]
user=www-data
environment=HOME="/home/www-data",USER="www-data"
process_name=%(program_name)s
numprocs=1
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes = 0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
directory=$ELASTICTM/src
command=celery
          --app RestApi.Celery.main_celery
          worker
          -l INFO
EOF

RUN <<EOF cat > ${ENTRYPOINT}
#!/bin/sh
set -e
echo "Start application processes using supervisord..."
exec "\$@"
EOF

RUN chmod +x ${ENTRYPOINT}

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
