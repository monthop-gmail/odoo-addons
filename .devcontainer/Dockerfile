FROM odoo:19.0
ENV TZ=Asia/Bangkok

USER root

# System packages
RUN apt-get update \
    && apt-get -y install git curl gcc libpython3-dev locales \
       fonts-tlwg-laksaman \
    && sed -i 's/# th_/th_/' /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*

# Python packages
RUN pip install --no-cache-dir --break-system-packages \
    git-aggregator promptpay

# Fix shell for odoo user (nologin → bash) so terminal works in Codespaces
RUN usermod -s /bin/bash odoo

# Git config for gitaggregate merges
RUN git config --global user.email "dev@thaiacc" \
    && git config --global user.name "ThaiACC Dev"

USER odoo
