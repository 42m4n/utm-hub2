# UTM-Automation

## Introduction

This repository is about creating applications to automate the process of applying tickets from ManageEngine, the ticket management app, into UTM (Fortigate).

![](utm-automation.png)

## Installation

To get started with the project using Docker, follow these steps:

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
   docker-compose up --pull -d
   ```

## API Endpoints

### 1. Create Terraform Files (v1)

- **Endpoint**: `/api/utm/v1/create_service`
- **Method**: POST
- **Description**: This endpoint is deprecated and contains unfixed bugs. It uses Terraform functions to search policies, which may lead to unreliable results. It is strongly recommended to use the v2 endpoint instead.

### 2. Create Terraform Files (v2)

- **Endpoint**: `/api/utm/v2/create_service`
- **Method**: POST
- **Parameters**:
  - Request body: JSON object containing the data
- **Example Request**:

    -   ```json
        {
          "content": "{\"request\": {\"id\": \"TKT123456\", \"udf_fields\": {\"udf_pick_5722\": \"utm1\", \"udf_sline_3013\": \"server1\", \"udf_pick_3016\": \"Grant\", \"udf_sline_4203\": \"HTTP,HTTPS\", \"udf_sline_4560\": \"User to Server\", \"udf_sline_3011\": \"user@example.com\"}}}"
        }
        ```
- **Example Response**:

    - ```json
        {"response": [{ "status": "ok" }]}
        ```

- **Description**: Creates Terraform files for UTM configuration based on the provided data. This endpoint processes the input, validates the UTM name, and generates the necessary Terraform files.

### 3. Get LDAP Groups

- **Endpoint**: `/api/utm/v1/groups`
- **Method**: GET
- **Parameters**:
  - *input_data*: JSON object containing search criteria
- **Example Request**:
    - ```bash
        GET /api/utm/ldap/groups?input_data={"list_info": {"search_fields": {"name": "admin"}}}
        ```
- **Description**: Retrieves LDAP groups based on the provided search criteria. This endpoint allows filtering groups by name.

### 4. Get UTM Services

- **Endpoint**: `/api/utm/ports`
- **Method**: GET
- **Parameters**:
  - `utm_name`: Name of the UTM
- **Description**:  Retrieves the list of services configured on a specified UTM.

### 5. Get UTM Interfaces

- **Endpoint**: `/api/utm/v1/interfaces`
- **Method**: GET
- **Parameters**:
  - `utm_name`: Name of the UTM
- **Description**: Retrieves the list of network interfaces configured on a specified UTM. This includes both physical and virtual interfaces.

### 6. Get UTM Policies

- **Endpoint**: `/api/utm/v1/sync`
- **Method**: GET
- **Parameters**:
  - `utm_name`: Name of the UTM (must match one of the configured UTMs in the system)
- **Description**: Retrieves the firewall policies from a specified UTM and stores them in Redis for quick access. This endpoint is useful for caching policy data to improve performance in subsequent operations.
