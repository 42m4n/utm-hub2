FROM repo.asax.ir/python:3.12-slim

WORKDIR /utm-automation

ENV TF_PLUGIN_CACHE_DIR="/root/.terraform.d/plugin-cache"

RUN ASA_REPO="https://repo.asax.ir/repository" \
    && sed -i 's/http:\/\/deb.debian.org/https:\/\/repo.asax.ir\/repository\/deb.debian.org/' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl unzip jq gnupg \
    && curl -fsSL ${ASA_REPO}/FileRepo/apt/packages.microsoft/gpgkey/microsoft.asc | gpg --dearmor | tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null \
    && echo "deb [arch=amd64,armhf,arm64] ${ASA_REPO}/packages.microsoft.com--ubuntu/20.04/prod focal main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends unixodbc-dev msodbcsql18 mssql-tools18 \
    && apt-get upgrade -y \
    && LATEST_TERRAFORM_VERSION=$(curl -s ${ASA_REPO}/releases.hashicorp.com/terraform/index.json | jq -r '.versions | keys | .[-1]') \
    && curl -o terraform.zip ${ASA_REPO}/releases.hashicorp.com/terraform/${LATEST_TERRAFORM_VERSION}/terraform_${LATEST_TERRAFORM_VERSION}_linux_amd64.zip \
    && unzip terraform.zip -d /usr/local/bin \
    && rm terraform.zip \
    && LATEST_PROVIDER_VERSION=$(curl -sSf ${ASA_REPO}/api.github.com//repos/fortinetdev/terraform-provider-fortios/releases | jq -r '.[0].tag_name') \
    && curl -o terraform-provider-fortios.zip ${ASA_REPO}/github.com/fortinetdev/terraform-provider-fortios/releases/download/${LATEST_PROVIDER_VERSION}/terraform-provider-fortios_${LATEST_PROVIDER_VERSION}_linux_amd64.zip \
    && mkdir -p ~/.terraform.d/plugin-cache \
    && mkdir -p ~/.terraform.d/plugins/registry.terraform.io/fortinetdev/fortios/${LATEST_PROVIDER_VERSION}/linux_amd64/ \
    && unzip terraform-provider-fortios.zip -d ~/.terraform.d/plugins/registry.terraform.io/fortinetdev/fortios/${LATEST_PROVIDER_VERSION}/linux_amd64/ \
    && rm terraform-provider-fortios.zip \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .