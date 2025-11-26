# syntax = docker/dockerfile:1.4.0

FROM docker.io/bitnamilegacy/spark:3.4 as spark

FROM node:latest as node

COPY . /app
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

COPY --from=node /app $ELASTICTM
WORKDIR $ELASTICTM

## LEGACY: The volume at /elastictm and the logs contained in it appear to never get used/modified.
#RUN mkdir -p $ELASTICTM_VOLUME/log/elastictm && \
#    touch $ELASTICTM_VOLUME/log/elastictm/gunicorn.log $ELASTICTM_VOLUME/log/elastictm/celery-worker.log && \
#    chmod -R oag+w $ELASTICTM_VOLUME/log/elastictm
## LEGACY: Due to the log files remaining empty, Logrotate will be passive in the container.
#RUN ln -s conf/logrotate.conf /etc/logrotate.d/activatm

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libboost-all-dev \
      libtercpp-dev \
      ruby \
      ruby-dev \
      zip \
      # LEGACY: The following packages MIGHT not be needed.
      # Either (a) they’re installed in the base image or (b) the application does not explicitly use them.
      apt-transport-https \
      apt-utils \
      build-essential \
      curl \
      default-jdk \
      default-jre \
      gfortran \
      git \
      iputils-ping \
      libatlas-base-dev \
      libblas-dev \
      libcurl4-openssl-dev \
      liblapack-dev \
      libssl-dev \
      libxml2-dev \
      libxslt1-dev \
      logrotate \
      nano \
      python3-bs4 \
      python3-matplotlib \
      python3-nose \
      python3-numpy \
      python3-pandas \
      python3-pip \
      python3-scipy \
      python3-sympy \
      software-properties-common \
      wget \
      supervisor

# LEGACY: The rubygem seems never used -- instead, source code from tools/pragmatic_segmenter-master is executed.
RUN gem install pragmatic_segmenter -v 0.3.23

# Download and install Kytea
WORKDIR /tmp
COPY ./tools/kytea/kytea-0.4.7.tar.gz .
RUN tar -xzf kytea-0.4.7.tar.gz
#RUN wget https://www.phontron.com/kytea/download/kytea-0.4.7.tar.gz && \
#    # TODO: Verify checksum before continuing?
#    tar -xzf kytea-0.4.7.tar.gz
WORKDIR /tmp/kytea-0.4.7
RUN if [ "$TARGETARCH" = "arm64" ] || [ "$TARGETARCH" = "arm32" ]; \
        then ./configure --build=aarch64-unknown-linux-gnu; \
        else ./configure; \
    fi && \
    make && \
    make install && \
    ldconfig

# Install Python dependencies
WORKDIR $ELASTICTM
RUN pip install --no-cache-dir -r requirements.txt

# If running on ARM architecture, download, build and install Mykytea-python from source (see https://github.com/chezou/Mykytea-python/pull/24)
WORKDIR /tmp/Mykytea-python
RUN if [ "$TARGETARCH" = "arm64" ] || [ "$TARGETARCH" = "arm32" ]; \
        then \
            apt-get install -y --no-install-recommends swig && \
            git clone https://github.com/chezou/Mykytea-python.git . && \
            git checkout 3a2818e && \
            # TODO: Verify checksum before continuing?
            make && \
            make install; \
    fi

# Download universal POS tagset
RUN python -m nltk.downloader -d /usr/share/nltk_data universal_tagset stopwords punkt

# Copy universal tag map to NTLK data directory
COPY tools/universal-pos-tags-master/*-treetagger-pg.map /usr/share/nltk_data/taggers/universal_tagset/

# Download, build and install Tercpp with custom monkey patching
WORKDIR $ELASTICTM/tools/pytercpp
COPY tools/pytercpp .
RUN git clone https://github.com/cservan/tercpp.git && \
    git -C tercpp checkout cef1e60 && \
    # TODO: Verify checksum before continuing?
    python setup.py build install

WORKDIR $ELASTICTM

# Start Gunicorn
#USER www-data
#WORKDIR $ELASTICTM/src/RestApi

# Create directory/files for Gunicorn logs
#WORKDIR $ELASTICTM/log
#RUN chmod 777 . && \
#    touch gunicorn.log && \
#    chmod 666 gunicorn.log
#CMD tail -f $ELASTICTM/log/gunicorn.log & \
#    cd $ELASTICTM/src && gunicorn \
#    -m 007 \
#    --bind 0.0.0.0:5000 \
#    --workers $GUNICORN_WORKERS \
#    --bind unix:/tmp/activatm.sock \
#    --error-logfile $ELASTICTM/log/gunicorn.log \
#    --access-logfile $ELASTICTM/log/gunicorn.log \
#    --capture-output \
#    --log-level INFO \
#     RestApi.Api:app

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

