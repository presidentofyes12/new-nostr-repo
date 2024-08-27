FROM ubuntu:22.04
ENV ODOO_VERSION 16.0
ENV OPENEDUCAT_VERSION 16.0
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev python3-venv \
    postgresql-client \
    nodejs npm \
    git \
    wget \
    libxml2-dev libxslt1-dev \
    libjpeg-dev libfreetype6-dev \
    libpq-dev \
    build-essential \
    libldap2-dev libsasl2-dev \
    libssl-dev \
    libffi-dev \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -d /opt/odoo -U -r -s /bin/bash odoo
RUN git clone https://github.com/odoo/odoo.git --depth 1 --branch ${ODOO_VERSION} /opt/odoo/odoo
RUN git clone https://github.com/openeducat/openeducat_erp.git --depth 1 --branch ${OPENEDUCAT_VERSION} /opt/odoo/openeducat
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r /opt/odoo/odoo/requirements.txt
RUN pip3 install cryptography pyopenssl==22.1.0 psycopg2-binary bs4 BeautifulSoup4 gitpython bech32
RUN pip3 install nostr
RUN cp -r /opt/odoo/openeducat/* /opt/odoo/odoo/addons/
COPY ./nostr_auth.py /opt/odoo/
COPY ./custom_odoo_server.py /opt/odoo/
COPY ./odoo_custom_addons /opt/odoo/custom_addons
RUN mkdir -p /etc/odoo
RUN mkdir -p /opt/ivcs_repos
RUN chown -R odoo:odoo /opt/odoo /etc/odoo /opt/ivcs_repos
RUN chmod +x /opt/odoo/custom_odoo_server.py
RUN mkdir -p /var/lib/odoo
RUN chown -R odoo:odoo /var/lib/odoo
USER odoo
RUN echo "from OpenSSL import crypto" > /tmp/patch_openssl.py
RUN echo "if not hasattr(crypto, 'X509_V_FLAG_EXPLICIT_POLICY'):" >> /tmp/patch_openssl.py
RUN echo "    crypto.X509_V_FLAG_EXPLICIT_POLICY = 0x8000" >> /tmp/patch_openssl.py
RUN echo "exec(open('/tmp/patch_openssl.py').read())" >> /opt/odoo/odoo/odoo/addons/base/models/ir_mail_server.py
CMD ["python3", "/opt/odoo/custom_odoo_server.py", "-c", "/etc/odoo/odoo.conf"]
