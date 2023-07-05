FROM debian:bullseye-slim

MAINTAINER Hakan Baysal <hakanbysl@gmail.com>

# ensure local python is preferred over distribution python
ENV PATH /usr/local/bin:$PATH

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

# runtime dependencies
RUN set -eux; \
	apt-get update; \
	apt-get install -y --no-install-recommends \
		ca-certificates \
		netbase \
		tzdata \
	; \
	rm -rf /var/lib/apt/lists/*

ENV GPG_KEY E3FF2839C048B25C084DEBE9B26995E310250568
ENV PYTHON_VERSION 3.9.17

RUN set -eux; \
	\
	savedAptMark="$(apt-mark showmanual)"; \
	apt-get update; \
	apt-get install -y --no-install-recommends \
		dpkg-dev \
		gcc \
		gnupg \
		libbluetooth-dev \
		libbz2-dev \
		libc6-dev \
		libdb-dev \
		libexpat1-dev \
		libffi-dev \
		libgdbm-dev \
		liblzma-dev \
		libncursesw5-dev \
		libreadline-dev \
		libsqlite3-dev \
		libssl-dev \
		make \
		tk-dev \
		uuid-dev \
		wget \
		xz-utils \
		zlib1g-dev \
	; \
	\
	wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz"; \
	wget -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc"; \
	GNUPGHOME="$(mktemp -d)"; export GNUPGHOME; \
	gpg --batch --keyserver hkp://keys.openpgp.org:80 --recv-keys "$GPG_KEY"; \
	gpg --batch --verify python.tar.xz.asc python.tar.xz; \
	gpgconf --kill all; \
	rm -rf "$GNUPGHOME" python.tar.xz.asc; \
	mkdir -p /usr/src/python; \
	tar --extract --directory /usr/src/python --strip-components=1 --file python.tar.xz; \
	rm python.tar.xz; \
	\
	cd /usr/src/python; \
	gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)"; \
	./configure \
		--build="$gnuArch" \
		--enable-loadable-sqlite-extensions \
		--enable-optimizations \
		--enable-option-checking=fatal \
		--enable-shared \
		--with-system-expat \
		--without-ensurepip \
	; \
	nproc="$(nproc)"; \
	EXTRA_CFLAGS="$(dpkg-buildflags --get CFLAGS)"; \
	LDFLAGS="$(dpkg-buildflags --get LDFLAGS)"; \
	LDFLAGS="${LDFLAGS:--Wl},--strip-all"; \
	make -j "$nproc" \
		"EXTRA_CFLAGS=${EXTRA_CFLAGS:-}" \
		"LDFLAGS=${LDFLAGS:-}" \
		"PROFILE_TASK=${PROFILE_TASK:-}" \
	; \
# https://github.com/docker-library/python/issues/784
# prevent accidental usage of a system installed libpython of the same version
	rm python; \
	make -j "$nproc" \
		"EXTRA_CFLAGS=${EXTRA_CFLAGS:-}" \
		"LDFLAGS=${LDFLAGS:--Wl},-rpath='\$\$ORIGIN/../lib'" \
		"PROFILE_TASK=${PROFILE_TASK:-}" \
		python \
	; \
	make install; \
	\
	cd /; \
	rm -rf /usr/src/python; \
	\
	find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
			-o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \
		\) -exec rm -rf '{}' + \
	; \
	\
	ldconfig; \
	\
	apt-mark auto '.*' > /dev/null; \
	apt-mark manual $savedAptMark; \
	find /usr/local -type f -executable -not \( -name '*tkinter*' \) -exec ldd '{}' ';' \
		| awk '/=>/ { so = $(NF-1); if (index(so, "/usr/local/") == 1) { next }; gsub("^/(usr/)?", "", so); print so }' \
		| sort -u \
		| xargs -r dpkg-query --search \
		| cut -d: -f1 \
		| sort -u \
		| xargs -r apt-mark manual \
	; \
	apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false; \
	rm -rf /var/lib/apt/lists/*; \
	\
	python3 --version

# make some useful symlinks that are expected to exist ("/usr/local/bin/python" and friends)
RUN set -eux; \
	for src in idle3 pydoc3 python3 python3-config; do \
		dst="$(echo "$src" | tr -d 3)"; \
		[ -s "/usr/local/bin/$src" ]; \
		[ ! -e "/usr/local/bin/$dst" ]; \
		ln -svT "$src" "/usr/local/bin/$dst"; \
	done

# if this is called "PIP_VERSION", pip explodes with "ValueError: invalid truth value '<VERSION>'"
ENV PYTHON_PIP_VERSION 23.0.1
# https://github.com/docker-library/python/issues/365
ENV PYTHON_SETUPTOOLS_VERSION 58.1.0
# https://github.com/pypa/get-pip
ENV PYTHON_GET_PIP_URL https://github.com/pypa/get-pip/raw/0d8570dc44796f4369b652222cf176b3db6ac70e/public/get-pip.py
ENV PYTHON_GET_PIP_SHA256 96461deced5c2a487ddc65207ec5a9cffeca0d34e7af7ea1afc470ff0d746207

RUN set -eux; \
	\
	savedAptMark="$(apt-mark showmanual)"; \
	apt-get update; \
	apt-get install -y --no-install-recommends wget; \
	\
	wget -O get-pip.py "$PYTHON_GET_PIP_URL"; \
	echo "$PYTHON_GET_PIP_SHA256 *get-pip.py" | sha256sum -c -; \
	\
	apt-mark auto '.*' > /dev/null; \
	[ -z "$savedAptMark" ] || apt-mark manual $savedAptMark > /dev/null; \
	apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false; \
	rm -rf /var/lib/apt/lists/*; \
	\
	export PYTHONDONTWRITEBYTECODE=1; \
	\
	python get-pip.py \
		--disable-pip-version-check \
		--no-cache-dir \
		--no-compile \
		"pip==$PYTHON_PIP_VERSION" \
		"setuptools==$PYTHON_SETUPTOOLS_VERSION" \
	; \
	rm -f get-pip.py; \
	\
	pip --version


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