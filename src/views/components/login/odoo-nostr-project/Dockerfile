FROM ubuntu:22.04
ENV ODOO_VERSION 16.0
ENV OPENEDUCAT_VERSION 16.0
ENV DEBIAN_FRONTEND noninteractive

# Install dependencies
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
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create Odoo user
RUN useradd -m -d /opt/odoo -U -r -s /bin/bash odoo

# Clone Odoo and OpenEduCat
RUN git clone https://github.com/odoo/odoo.git --depth 1 --branch ${ODOO_VERSION} /opt/odoo/odoo
RUN git clone https://github.com/openeducat/openeducat_erp.git --depth 1 --branch ${OPENEDUCAT_VERSION} /opt/odoo/openeducat

# Install Python dependencies
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r /opt/odoo/odoo/requirements.txt
RUN pip3 install cryptography pyopenssl==22.1.0 psycopg2-binary bs4 BeautifulSoup4 gitpython bech32 websocket-client websockets
RUN pip3 install nostr

# Copy OpenEduCat addons
RUN cp -r /opt/odoo/openeducat/* /opt/odoo/odoo/addons/

# Copy custom files
COPY ./nostr_auth.py /opt/odoo/
COPY ./custom_odoo_server.py /opt/odoo/
COPY ./odoo_custom_addons /opt/odoo/custom_addons
COPY ./check_nostr_bridge.sh /opt/odoo/check_nostr_bridge.sh

# Set up directories and permissions
RUN mkdir -p /etc/odoo /opt/ivcs_repos /var/lib/odoo /opt/odoo/.local/share/Odoo/filestore /opt/odoo/.local/share/Odoo/sessions
RUN chown -R odoo:odoo /opt/odoo /etc/odoo /opt/ivcs_repos /var/lib/odoo
RUN chmod +x /opt/odoo/check_nostr_bridge.sh /opt/odoo/custom_odoo_server.py

# Switch to odoo user
USER odoo

# Patch OpenSSL
RUN echo "from OpenSSL import crypto" > /tmp/patch_openssl.py && \
    echo "if not hasattr(crypto, 'X509_V_FLAG_EXPLICIT_POLICY'):" >> /tmp/patch_openssl.py && \
    echo "    crypto.X509_V_FLAG_EXPLICIT_POLICY = 0x8000" >> /tmp/patch_openssl.py && \
    echo "exec(open('/tmp/patch_openssl.py').read())" >> /opt/odoo/odoo/odoo/addons/base/models/ir_mail_server.py

# Initialize the database and start Odoo
CMD ["/bin/bash", "-c", "\
    /opt/odoo/check_nostr_bridge.sh && \
    python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo/odoo.conf -d odoodb -i base && \
    python3 /opt/odoo/custom_odoo_server.py -c /etc/odoo/odoo.conf \
    "]
