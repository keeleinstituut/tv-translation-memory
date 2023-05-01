FROM debian:11
MAINTAINER Pangeanic <info@pangeanic.com>
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get update && apt-get install -y git

# Install dependencies
RUN apt-get install -y python3-pip && pip3 install virtualenv
RUN apt-get install -y procps

# Activate VirtualEnv in 'venv' directory
# TODO (not working now): RUN virtualenv $ELASTICTM/venv && . $ELASTICTM/venv/bin/activate

# Install packages
RUN apt-get install -y libxml2-dev libxslt1-dev python-dev python3-bs4 libcurl4-openssl-dev apt-transport-https zip
RUN apt-get install -y libblas-dev liblapack-dev libatlas-base-dev gfortran libssl-dev
RUN apt-get install -y python3-numpy python3-scipy python3-matplotlib python3-ipython python3-pandas python3-sympy python3-nose
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils software-properties-common
# Install Java
RUN apt-get install -y default-jre default-jdk

# Install & configure ElasticSearch
RUN apt-get install -y wget
RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
#RUN echo "deb https://packages.elastic.co/elasticsearch/2.x/debian stable main" | tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list
RUN apt-get install apt-transport-https
RUN echo "deb https://artifacts.elastic.co/packages/6.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-6.x.list
RUN apt-get update && apt-get install -y --force-yes elasticsearch
#RUN /usr/share/elasticsearch/bin/plugin install mobz/elasticsearch-head

# # Install Redis
# RUN echo "deb http://packages.dotdeb.org bullseye all" | tee -a /etc/apt/sources.list.d/dotdeb.org.list
# RUN apt-get update && apt-get install -y --force-yes redis-server
# # Remove sources as they conflict with nginx installation
# RUN rm /etc/apt/sources.list.d/dotdeb.org.list && apt-get update
RUN apt install -y --force-yes redis-server

# Install Apache Spark
RUN apt-get install -y scala
RUN wget https://archive.apache.org/dist/spark/spark-1.6.3/spark-1.6.3-bin-hadoop2.6.tgz
RUN tar xzf spark-1.6.3-bin-hadoop2.6.tgz && mv spark-1.6.3-bin-hadoop2.6 /opt/

# # Install PostgreSQL
# ENV LSB_RELEASE bullseye
# RUN sh -c 'echo "deb http://apt-archive.postgresql.org/pub/repos/apt/ ${LSB_RELEASE}-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
# RUN apt-get update

# ENV PSQL_VERSION 11
# RUN apt-get install -y --allow-unauthenticated postgresql-${PSQL_VERSION} postgresql-server-dev-${PSQL_VERSION}
RUN apt update
RUN apt install -y --force-yes vim curl gpg gnupg2 software-properties-common apt-transport-https lsb-release ca-certificates
RUN curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" | tee  /etc/apt/sources.list.d/pgdg.list
RUN apt update
ENV PSQL_VERSION 11
RUN apt install -y --force-yes --allow-unauthenticated postgresql-${PSQL_VERSION} postgresql-server-dev-${PSQL_VERSION}


# Install Ruby
RUN apt-get install -y ruby ruby-dev

# Install & configure Api doc generator
RUN apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -
RUN apt-get install -y nodejs
RUN npm install apidoc -g

# Install & configure nginx
RUN apt-get install -y nginx

# Install & configure logrotate
RUN apt-get install -y logrotate

# Install & setup Supervisord
RUN apt-get install -y supervisor

# RUN apt-get remove -y python-pip python3-pip
# RUN wget https://bootstrap.pypa.io/pip/2.7/get-pip.py
# RUN python get-pip.py
# # RUN wget https://bootstrap.pypa.io/get-pip.py
# RUN python3 get-pip.py

# Install Python packages
RUN pip3 install flask flask_restful flask_principal flask_jwt celery flower flask_sqlalchemy langid networkx babel "elasticsearch>=6.0.0,<7.0.0" "elasticsearch_dsl>=6.0.0,<7.0.0" iso639 couchdb pymongo redis lxml zipstream uwsgi kytea requests requests-toolbelt  treetaggerwrapper nltk pyyaml editdistance translate future pyresttest psycopg2 pexpect microsofttranslator CMRESHandler
RUN pip3 install theano gunicorn

# Download universtal POS tagset
RUN python3 -m nltk.downloader universal_tagset stopwords punkt
RUN mv /root/nltk_data /usr/share/nltk_data

RUN apt-get install -y nano libboost-all-dev

############################ Clone the repo ##############################
ENV ELASTICTM /opt/elastictm
ENV ELASTICTM_VOLUME /elastictm

# Setup PostgreSQL database
USER postgres
RUN /etc/init.d/postgresql start &&  psql -c "create database activatm"
USER root

# Clone the conf files into the docker container
RUN echo " Cloning----"
RUN echo " ==== ...."
RUN git clone --recursive -b feature/#216/setup-nectm https://github.com/keeleinstituut/tv-translation-memory.git $ELASTICTM
WORKDIR $ELASTICTM
RUN cd $ELASTICTM
#################################################################
RUN cd tools/pytercpp && git clone https://github.com/cservan/tercpp.git
# Copy universal tag map to NTLK data directory
RUN cp tools/universal-pos-tags-master/*-treetagger-pg.map /usr/share/nltk_data/taggers/universal_tagset/


# Build & install pytercpp
RUN ( cd tools/pytercpp; python3 setup.py build install )

# Build & generate pragmatic-segmenter
RUN ( cd tools/pragmatic_segmenter-master; gem install pragmatic_segmenter )

# Generate API documentation
RUN ( cd src/RestApi/; node --harmony `which apidoc` -i . -o ../../doc )

# Setup UWSGI
RUN mkdir -p $ELASTICTM_VOLUME/log/elastictm && touch $ELASTICTM_VOLUME/log/elastictm/gunicorn.log $ELASTICTM_VOLUME/log/elastictm/celery-worker.log
RUN chmod -R oag+w $ELASTICTM_VOLUME/log/elastictm

# Setting Celery as a daemon
#RUN touch $ELASTICTM_VOLUME/log/elastictm/celery-worker.log


#################### Copy service configurations ############
RUN cp conf/nginx.conf /etc/nginx/sites-available/elastictm.conf
RUN ln -s /etc/nginx/sites-available/elastictm.conf /etc/nginx/sites-enabled/

RUN cp conf/logrotate.conf /etc/logrotate.d/activatm
# Configure ElasticSearch
RUN cp conf/elasticsearch.yml /etc/elasticsearch/
RUN echo "path.data: /elasticsearch_data" >> /etc/elasticsearch/elasticsearch.yml
RUN echo "path.repo: /elasticsearch_data/backup" >> /etc/elasticsearch/elasticsearch.yml

RUN mkdir /opt/elasticsearch/ && chown -R elasticsearch /opt/elasticsearch/
RUN mkdir -p $ELASTICTM_VOLUME/log/elasticsearch/ && mkdir -p $ELASTICTM_VOLUME/es_data && chown -R elasticsearch $ELASTICTM_VOLUME/log/elasticsearch/ $ELASTICTM_VOLUME/es_data
RUN mkdir -p $ELASTICTM_VOLUME/log/activatm/
RUN mkdir /elasticsearch_data && chown -R elasticsearch /elasticsearch_data

# For convenience
RUN echo '"\en": history-search-forward' > ~/.inputrc
RUN echo '"\ep": history-search-backward' >> ~/.inputrc

# Setup supervisord
RUN cp conf/supervisord.conf /etc/supervisor/conf.d/activatm.conf

RUN cp docker/wait-for-postgres.sh ~/
# Create activatm user (Celery is run under it)
RUN useradd -ms /bin/bash activatm
RUN pip3 install tornado
RUN echo  "#! /bin/bash\n/etc/init.d/postgresql start; ~/wait-for-postgres.sh ; su postgres -c \"psql -c \\\"create user activatm; alter user activatm with password 'activatm' \\\"\" ; chown -R elasticsearch:elasticsearch /elasticsearch_data; service elasticsearch start;  supervisord "  > run.sh
RUN chmod +x run.sh
# Run Supervisor - responsible to start up & keep alive all services:
# - ElasticSearch, Nginx, uWSGI, Celery, Redis
CMD ["./run.sh"]
 # ES port
EXPOSE 9200
# API port (via nginx)
EXPOSE 7979
# API documentation port (via nginx)
EXPOSE 7878

VOLUME $ELASTICTM_VOLUME
