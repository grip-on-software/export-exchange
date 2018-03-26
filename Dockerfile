FROM python:2.7-alpine3.7

COPY requirements.txt /tmp/

RUN addgroup agent && adduser -s /bin/bash -D -G agent agent && \
	apk --update add gcc musl-dev gnupg libgpg-error-dev gpgme gpgme-dev bash openssl-dev swig && \
	pip install -r /tmp/requirements.txt && \
	apk del gcc musl-dev openssl-dev && rm -rf /var/cache/apk/* /tmp/ /root/.cache

RUN mkdir /home/agent/exchange
COPY exchange/upload.py /home/agent/exchange

VOLUME /home/agent/.gnupg
VOLUME /home/agent/upload
WORKDIR /home/agent

CMD ["/bin/bash"]
