FROM python:3.11
WORKDIR /utm-automation
RUN apt update
RUN apt install -y curl

RUN sh -c "curl -s https://packages.microsoft.com/keys/microsoft.asc | apt-key add -" \
    && sh -c "curl -s https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list" \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18 unixodbc-dev unixodbc

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN LATEST_TERRAFORM_VERSION=$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | grep -Po '"current_version":.*?[^\\]",' | awk -F'"' '{print $4}') \
    && curl -o /opt/terraform.zip https://releases.hashicorp.com/terraform/${LATEST_TERRAFORM_VERSION}/terraform_${LATEST_TERRAFORM_VERSION}_linux_amd64.zip \
    && unzip /opt/terraform.zip -d /bin \
    && rm /opt/terraform.zip

COPY terraform /opt/terraform
COPY infra-api/ infra-api/
COPY queue_executor/ queue_executor/