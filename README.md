# UTM-Automation 
## Introduction
This repository is about creating applications to automate the process of applying tickets from ManageEngine, the ticket management app, into UTM (Fortigate).

![](utm-automation.png)
## Installation

To get started with the UTM Hub using Docker, follow these steps:

1. **Clone the repository**:
    ```bash
    git clone https://gitops.asax.ir/infrastructure-automation-team/security-automation/access-rule-automation/utm-automation.git
    cd utm-automation
    ```

2. **Set up environment variables**:
    Edit the `.env` file in the root directory and add the necessary environment variables.

3. **Docker compose services**:
    If you have external `Redis` or `RabbitMQ`, comment them from the `docker-compose.yml` file.

4. **Build and run the Docker containers**:
    ```bash
    docker-compose up --build -d
    ```