FROM centos:centos7

MAINTAINER Tetsuya Oikawa <tetsuya.oikawa@ctc-g.co.jp>

RUN yum -y update

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
  git

RUN yum clean all

RUN curl -L http://stedolan.github.io/jq/download/linux64/jq > /usr/local/bin/jq && \
  chmod +x /usr/local/bin/jq

RUN curl -kL https://bootstrap.pypa.io/get-pip.py | python

RUN pip install -U setuptools pip
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm -f /tmp/requirements.txt

ENV APPDIR /app
WORKDIR ${APPDIR}
COPY ./ ${APPDIR}
RUN python setup.py install

RUN mkdir -p /etc/rack /var/log/rack /var/lib/rack/lock
COPY ./etc/api-paste.ini /etc/rack/api-paste.ini
COPY ./tools/setup/rack.conf /etc/rack/rack.conf

EXPOSE 8088

COPY ./tools/setup/docker-init.sh /usr/local/bin/init.sh
RUN chmod u+x /usr/local/bin/init.sh
CMD ["/usr/local/bin/init.sh"]
