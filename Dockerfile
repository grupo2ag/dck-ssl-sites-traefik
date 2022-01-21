# Python CRM - AC
FROM python:3.8-alpine

# Label imagem
LABEL VERSION="0.0.1"
LABEL NAME="hml-ac-cad-cliente-crm-backend-service"
LABEL MAINTAINER="infra2@autocrivo.com."

ARG mode
RUN if [ "x$mode" = "xdev" ] ; then echo "Development" ; else echo "Production" ; fi

# File requirements install pip
COPY ./requirements.txt /tmp/requirements.txt

# Install dependency

RUN apk --update add bash \
      nano \
      gcc  \
      git \
      curl \
      linux-headers \
      musl-dev \
      libffi-dev \
      py-pip \
      mariadb-connector-c-dev \
      && pip install -r /tmp/requirements.txt

#RUN mkdir -p /opt/crm/
RUN git clone -b teste https://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@github.com/grupo2ag/dck-ssl-sites-traefik.git /var/crm/ 
WORKDIR /var/crm/
RUN chmod -Rf 765 /var/crm/*


# Expose Port

EXPOSE 56737 5000

# Execut aplication Python

CMD ["/var/crm/cad.py"]


# Entrypoint

ENTRYPOINT ["python", "cad.py"]
