FROM python:3.9.17-bullseye

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get update && apt-get install -y git

# Install packages
RUN apt-get install -y libxml2-dev libxslt1-dev python3-bs4 libcurl4-openssl-dev apt-transport-https zip libtercpp-dev
RUN apt-get install -y libblas-dev liblapack-dev libatlas-base-dev gfortran libssl-dev
RUN apt-get install -y python3-numpy python3-scipy python3-matplotlib python3-pandas python3-sympy python3-nose
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils software-properties-common iputils-ping
# Install Java
RUN apt-get install -y default-jre default-jdk

# Install Ruby
RUN apt-get install -y ruby ruby-dev

# Install & configure Api doc generator
RUN apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -
RUN apt-get install -y nodejs
RUN npm install apidoc -g

# Install & configure logrotate
RUN apt-get install -y logrotate

# Install & setup Supervisord
RUN apt-get install -y supervisor

RUN apt-get update \
    && apt-get install -y python3-pip build-essential

############################ Clone the repo ##############################
ENV ELASTICTM /opt/elastictm
ENV ELASTICTM_VOLUME /elastictm

# Clone the conf files into the docker container
RUN echo " Cloning----"
RUN echo " ==== ...."
COPY . $ELASTICTM
WORKDIR $ELASTICTM
RUN cd $ELASTICTM

#################################################################

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt


RUN apt-get install -y wget
RUN cd /tmp && \
    wget http://www.phontron.com/kytea/download/kytea-0.4.7.tar.gz && \
    tar xzf kytea-0.4.7.tar.gz && \
    cd /tmp/kytea-0.4.7/ && \
    # ./configure && \ # This is for x86
    ./configure --build=aarch64-unknown-linux-gnu && \
    make && \
    make install && \
    pip3 install kytea

# Download universtal POS tagset
RUN python3 -m nltk.downloader universal_tagset stopwords punkt
RUN mv /root/nltk_data /usr/share/nltk_data

RUN apt-get install -y nano libboost-all-dev

RUN cd tools/pytercpp &&  \
    git clone https://github.com/cservan/tercpp.git
# Copy universal tag map to NTLK data directory
RUN cp tools/universal-pos-tags-master/*-treetagger-pg.map /usr/share/nltk_data/taggers/universal_tagset/


# Build & install pytercpp
RUN cd tools/pytercpp && \
    python3 setup.py build install

# Build & generate pragmatic-segmenter
RUN cd tools/pragmatic_segmenter-master && \
    gem install pragmatic_segmenter

# Generate API documentation
RUN cd src/RestApi/ && \
    node --harmony `which apidoc` -i . -o ../../doc

# Setup UWSGI
RUN mkdir -p $ELASTICTM_VOLUME/log/elastictm && \
    touch $ELASTICTM_VOLUME/log/elastictm/gunicorn.log $ELASTICTM_VOLUME/log/elastictm/celery-worker.log
RUN chmod -R oag+w $ELASTICTM_VOLUME/log/elastictm

#################### Copy service configurations ############
RUN cp conf/logrotate.conf /etc/logrotate.d/activatm

# Setup supervisord
RUN cp conf/supervisord.conf /etc/supervisor/conf.d/activatm.conf

RUN cp docker/wait-for-postgres.sh ~/
# Create activatm user (Celery is run under it)
RUN useradd -ms /bin/bash activatm

RUN npm install http-server -g
RUN echo  "#! /bin/bash\n supervisord"  > run.sh
RUN echo  "#! /bin/bash\n http-server /opt/elastictm/doc --port 3050"  > rundocs.sh
RUN echo  "#! /bin/bash\n python3 /opt/elastictm/src/RestApi/Api.py"  > runapi.sh

RUN mkdir -p $ELASTICTM/log \
    && touch $ELASTICTM/log/gunicorn.log \
    && chmod 666 $ELASTICTM/log/gunicorn.log

# Run Supervisor - responsible to start up & keep alive all services:
RUN chmod +x run.sh && \
    chmod +x rundocs.sh && \
    chmod +x runapi.sh && \
    chmod 777 $ELASTICTM/log

ENTRYPOINT ["./run.sh"]

EXPOSE 3050
EXPOSE 5000
VOLUME $ELASTICTM_VOLUME
