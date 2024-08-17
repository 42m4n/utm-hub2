FROM python:3.11
WORKDIR /utm-automation
RUN apt update
RUN apt install -y curl

RUN sh -c "curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -" \
    && apt-get update \
    && sh -c "curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list" \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && ACCEPT_EULA=Y apt-get install -y mssql-tools18

RUN apt install -y unixodbc
RUN apt install -y unixodbc-dev
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

