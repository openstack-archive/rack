FROM centos:centos6

MAINTAINER Tetsuya Oikawa <tetsuya.oikawa@ctc-g.co.jp>

RUN yum -y update && yum -y install https://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm

RUN yum -y install \
  libffi-devel \
  libgcc-devel \
  gcc \
  python-devel \
  python-lxml \
  libxslt-devel \
  libxml2-devel \
  openssl-devel \
  MySQL-python \
  python-pip \
  git

RUN yum clean all

RUN curl -L http://stedolan.github.io/jq/download/linux64/jq > /usr/local/bin/jq
RUN chmod +x /usr/local/bin/jq

ENV APPDIR /app
WORKDIR ${APPDIR}

RUN pwd
ADD ./ ${APPDIR}
RUN pip install -U setuptools pip
RUN pip install -r requirements.txt
RUN python setup.py install

RUN mkdir -p /etc/rack /var/log/rack /var/lib/rack/lock
COPY /etc/api-paste.ini /etc/rack/api-paste.ini
COPY /tools/setup/rack.conf /etc/rack/rack.conf

EXPOSE 8088

ADD tools/setup/docker-init.sh /usr/local/bin/init.sh
RUN chmod u+x /usr/local/bin/init.sh
CMD ["/usr/local/bin/init.sh"]
