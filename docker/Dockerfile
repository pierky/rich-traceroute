FROM ubuntu:latest

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get install \
        -y \
        --no-install-recommends \
            vim \
            git \
            build-essential \
            nginx \
            supervisor \
            python3-dev \
            python3-pip && \
    rm -rf /var/lib/apt/lists/*

# To have /etc/protocols, required by eventlet
RUN apt-get update && \
    apt-get -o Dpkg::Options::="--force-confmiss" install --reinstall netbase

RUN rm /etc/nginx/sites-enabled/default

RUN mkdir /var/log/rich_traceroute
RUN chown -R www-data:www-data /var/log/rich_traceroute

RUN mkdir /var/log/gunicorn
RUN chown -R www-data:www-data /var/log/gunicorn

RUN pip3 install --upgrade \
    pip \
    setuptools \
    wheel \
    gunicorn \
    eventlet

RUN mkdir /app

# Requirements
# -----------------------------------
# Copy only the requirements.txt first, so Docker will not
# install all the requirements every time the image is built
# just because the `COPY . /app/` layer is invalidated.

COPY requirements.txt /app/
WORKDIR /app
RUN pip3 install -r requirements.txt

# Configuration files
# -----------------------------------

COPY docker/rich_traceroute.yml /etc/rich_traceroute.yml

COPY docker/nginx.conf /etc/nginx/sites-enabled/rich_traceroute

COPY docker/gunicorn.conf.py /etc/gunicorn.conf.py

COPY docker/supervisord.conf /etc/supervisord.conf

# Prep the container for Let's Encrypt
# -----------------------------------

RUN mkdir /etc/letsencrypt

# Full repository
# -----------------------------------

COPY . /app/

EXPOSE 80

CMD ["/usr/bin/supervisord"]
