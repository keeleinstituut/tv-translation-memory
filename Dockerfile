# syntax = docker/dockerfile:1.4.0

FROM docker.io/bitnamilegacy/spark:3.4 as spark

FROM node:latest as node

COPY src/RestApi /app/src/RestApi
RUN npm install apidoc -g

WORKDIR /app/src/RestApi
RUN apidoc -i . -o ../../doc_build

FROM python:3.9.17-bullseye

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

RUN pip install --no-cache-dir -r requirements.txt

# Download, build and install Mykytea-python from source
# This is required for ARM (see https://github.com/chezou/Mykytea-python/pull/24)
# For other architectures, we build from source after pip install to ensure
# the Mykytea module is properly installed (pip package kytea may not work correctly)
WORKDIR /tmp/Mykytea-python
RUN git clone https://github.com/chezou/Mykytea-python.git . && \
    git checkout 3a2818e && \
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

RUN python -m nltk.downloader -d /usr/share/nltk_data universal_tagset stopwords punkt

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
