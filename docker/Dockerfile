FROM debian:11
MAINTAINER Pangeanic <info@pangeanic.com>
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get update && apt-get install -y git

# Install dependencies
RUN apt-get install -y python3-pip && pip3 install virtualenv

# Activate VirtualEnv in 'venv' directory

# Install packages
RUN apt-get install -y libxml2-dev libxslt1-dev python3-dev python3-bs4 libcurl4-openssl-dev apt-transport-https zip libtercpp-dev
RUN apt-get install -y libblas-dev liblapack-dev libatlas-base-dev gfortran libssl-dev
RUN apt-get install -y python3-numpy python3-scipy python3-matplotlib python3-pandas python3-sympy python3-nose python3-dev
RUN pip3 install ipython
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

# Install Python packages

RUN pip3 install flask flask_restful flask_principal flask_jwt 
RUN pip3 install flower flask_sqlalchemy langid networkx babel
RUN pip3 install iso639 couchdb pymongo redis lxml zipstream uwsgi requests requests-toolbelt  
RUN pip3 install treetaggerwrapper nltk pyyaml editdistance translate future pyresttest 
RUN pip3 install psycopg2-binary pexpect microsofttranslator
RUN pip3 install celery CMRESHandler
RUN pip3 install theano gunicorn chardet
RUN pip3 install opensearch-py opensearch-dsl

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

############################ Clone the repo ##############################
ENV ELASTICTM /opt/elastictm
ENV ELASTICTM_VOLUME /elastictm

# Clone the conf files into the docker container
RUN echo " Cloning----"
RUN echo " ==== ...."
COPY . $ELASTICTM
WORKDIR $ELASTICTM
RUN cd $ELASTICTM

# Uninstall new elasticsearch
RUN pip uninstall --yes elasticsearch && \
    pip3 install elasticsearch==7.13.4

#################################################################

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

RUN mkdir -p $ELASTICTM/log

# Run Supervisor - responsible to start up & keep alive all services:
RUN chmod +x run.sh && \
    chmod +x rundocs.sh && \
    chmod +x runapi.sh && \
    chmod 777 $ELASTICTM/log

ENTRYPOINT ["./run.sh"]

EXPOSE 3050
EXPOSE 5000
VOLUME $ELASTICTM_VOLUME