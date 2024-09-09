import json
import os

import redis


class BaseSetting:
    debug = os.getenv("DJANGO_DEBUG", "false").lower() == "true"


class Terraform:
    # DEBUG FALSE
    terraform_base_path = os.getenv("TERRAFORM_BASE_PATH", "/opt/terraform/")
    terraform_resources_path = os.getenv(
        "TERRAFORM_RESOURCES_PATH", "/opt/terraform_resources/"
    )
    terraform_queue_path = os.getenv(
        "TERRAFORM_QUEUE_PATH", "/opt/terraform_queue/queue.json"
    )
    terraform_log_path = os.getenv("TERRAFORM_LOG_PATH", "/opt/terraform_log/logs.json")

    # DEBUG TRUE
    local_terraform_base_path = os.getenv(
        "LOCAL_TERRAFORM_BASE_PATH", "/utm-automation/terraform/"
    )
    local_terraform_resources_path = os.getenv(
        "LOCAL_TERRAFORM_RESOURCES_PATH", "/utm-automation/terraform_resources/"
    )
    local_terraform_queue_path = os.getenv(
        "LOCAL_TERRAFORM_QUEUE_PATH", "./terraform_queue/queue.json"
    )
    local_terraform_log_path = os.getenv(
        "LOCAL_TERRAFORM_LOG_PATH", "./terraform_log/logs.json"
    )

    delay = int(os.getenv("TERRAFORM_DELAY", 10))


class ManageEngine:
    manage_engine_address = os.getenv("MANAGE_ENGINE_ADDRESS", "https://172.20.29.194")
    manage_engine_token = os.getenv(
        "MANAGE_ENGINE_TOKEN", "6619FACD-CB5D-430A-B564-705D0887E7D1"
    )
    manage_engine_done_status = os.getenv("MANAGE_ENGINE_DONE_STATUS", "4")


class Redis:
    host = os.getenv("REDIS_HOST", "localhost")
    port = os.getenv("REDIS_PORT", 6379)
    db = os.getenv("REDIS_DB", 1)
    queue_name = os.getenv("REDIS_QUEUE_NAME", "utm_queue")
    redis_client = redis.Redis(host=host, port=port, db=db)


class ElasticSearch:
    host = os.getenv("ELASTIC_HOST", "http://st-log-elk")
    port = os.getenv("ELASTIC_PORT", 9200)
    index = os.getenv("ELASTIC_INDEX", "utm_automation_log")
    pipeline = os.getenv("ELASTIC_PIPELINE", "DateChanger")
    api_key = os.getenv(
        "ELASTIC_API_KEY",
        "NzJYMWZJMEJMT2dZcnQ5Ri1lUTQ6dTE0MDZQSk1SbkMyeG5NUWMzQjNvQQ==",
    )


class RabbitMQ:
    # host = os.getenv("RABBITMQ_HOST", "http://st-log-elk")
    host = os.getenv("RABBITMQ_HOST", "172.28.33.6")
    port = os.getenv("RABBITMQ_PORT", 5672)
    exchange = os.getenv("RABBITMQ_EXCHANGE", "utm_automation_log")
    routing_key = os.getenv("RABBITMQ_ROUTING_KEY", "logstash")
    username = os.getenv("RABBITMQ_USERNAME", "pusheradmin")
    password = os.getenv("RABBITMQ_PASSWORD", "1qaz!QAZ")
    queue_name = os.getenv("RABBITMQ_QUEUE_NAME", "utm_automation_log")


class UTM:
    utms = json.loads(
        os.getenv(
            "UTMS", """[
                    {"UTM_NAME":"UTM-Test","UTM_ADDRESS":"172.20.26.148","UTM_TOKEN":"60xnNkpdfz70H756h1m5HdrbQc4wkm"}
                ]"""))
