FROM python:3.9.17-bullseye

ARG TARGETARCH
ENV DEBIAN_FRONTEND noninteractive
ENV ELASTICTM /opt/elastictm
ENV ELASTICTM_VOLUME /elastictm
ENV GUNICORN_WORKERS 4
VOLUME $ELASTICTM_VOLUME

# LEGACY: This user never appears to be used for anything.
RUN useradd -ms /bin/bash activatm

# LEGACY: The volume at /elastictm and the logs contained in it appear to never get used/modified.
RUN mkdir -p $ELASTICTM_VOLUME/log/elastictm && \
    touch $ELASTICTM_VOLUME/log/elastictm/gunicorn.log $ELASTICTM_VOLUME/log/elastictm/celery-worker.log && \
    chmod -R oag+w $ELASTICTM_VOLUME/log/elastictm
# LEGACY: Due to the log files remaining empty, Logrotate will be passive in the container.
COPY conf/logrotate.conf /etc/logrotate.d/activatm

# Create directory/files for Gunicorn logs
WORKDIR $ELASTICTM/log
RUN chmod 777 . && \
    touch gunicorn.log && \
    chmod 666 gunicorn.log

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libboost-all-dev=1.74.0.3 \
      libtercpp-dev=0.6.2+svn46-1.1+b1 \
      ruby=1:2.7+2 \
      ruby-dev=1:2.7+2 \
      zip=3.0-12 \
      # LEGACY: The following packages MIGHT not be needed.
      # Either (a) they’re installed in the base image or (b) the application does not explicitly use them.
      apt-transport-https=2.2.4 \
      apt-utils=2.2.4 \
      build-essential=12.9 \
      curl=7.74.0-1.3+deb11u7 \
      default-jdk=2:1.11-72 \
      default-jre=2:1.11-72 \
      gfortran=4:10.2.1-1 \
      git=1:2.30.2-1+deb11u2 \
      iputils-ping=3:20210202-1 \
      libatlas-base-dev=3.10.3-10 \
      libblas-dev=3.9.0-3 \
      libcurl4-openssl-dev=7.74.0-1.3+deb11u7 \
      liblapack-dev=3.9.0-3 \
      libssl-dev=1.1.1n-0+deb11u5 \
      libxml2-dev=2.9.10+dfsg-6.7+deb11u4 \
      libxslt1-dev=1.1.34-4+deb11u1 \
      logrotate=3.18.0-2+deb11u1 \
      nano=5.4-2+deb11u2 \
      python3-bs4=4.9.3-1 \
      python3-matplotlib=3.3.4-1 \
      python3-nose=1.3.7-7 \
      python3-numpy=1:1.19.5-1 \
      python3-pandas=1.1.5+dfsg-2 \
      python3-pip=20.3.4-4+deb11u1 \
      python3-scipy=1.6.0-2 \
      python3-sympy=1.7.1-3 \
      software-properties-common=0.96.20.2-2.1 \
      wget=1.21-1+deb11u1

# LEGACY: The rubygem seems never used -- instead, source code from tools/pragmatic_segmenter-master is executed.
RUN gem install pragmatic_segmenter -v 0.3.23

# Download and install Kytea
WORKDIR /tmp
RUN wget https://www.phontron.com/kytea/download/kytea-0.4.7.tar.gz && \
    # TODO: Verify checksum before continuing?
    tar -xzf kytea-0.4.7.tar.gz
WORKDIR /tmp/kytea-0.4.7
RUN if [ "$TARGETARCH" = "arm64" ] || [ "$TARGETARCH" = "arm32" ]; \
        then ./configure --build=aarch64-unknown-linux-gnu; \
        else ./configure; \
    fi && \
    make && \
    make install && \
    ldconfig

# Install Python dependencies
WORKDIR /tmp
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# If running on ARM architecture, download, build and install Mykytea-python from source (see https://github.com/chezou/Mykytea-python/pull/24)
WORKDIR /tmp/Mykytea-python
RUN if [ "$TARGETARCH" = "arm64" ] || [ "$TARGETARCH" = "arm32" ]; \
        then \
            apt-get install -y --no-install-recommends swig=4.0.2-1 && \
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

COPY docker/wait-for-postgres.sh ~/

COPY . $ELASTICTM

# Start Gunicorn
USER www-data
WORKDIR $ELASTICTM/src/RestApi
CMD gunicorn \
    -m 007 \
    --bind 0.0.0.0:5000 \
    --workers $GUNICORN_WORKERS \
    --bind unix:/tmp/activatm.sock \
    --error-logfile $ELASTICTM/log/gunicorn.log \
    --access-logfile $ELASTICTM/log/gunicorn.log \
    --capture-output \
    --log-level INFO \
     Api:app
