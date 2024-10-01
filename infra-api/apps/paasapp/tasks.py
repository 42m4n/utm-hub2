import json
import logging
import os
import shutil

from django.conf import settings
from python_terraform import Terraform as tf

from apps.paasapp.modules.terraform import (
    create_requests_obj,
    fill_trf_fields,
    generate_unique_name,
)
from common.conf import BaseSetting
from common.conf import Redis as RedisConf
from common.conf import Terraform
from common.logger import logger
from InfraApp.celery import celery_app

from .modules.terraform import convert_policies_to_terraform_file
from .modules.utm import (
    UTMHandler,
    filter_utm_policies_services_destination,
    filter_utm_policies_source_destination,
)


@celery_app.task(name="create_tf_files")
def create_tf_files(resources, ticket_number):
    logger.info(f"Creating terraform files for ticket {ticket_number}")
    queue_obj = create_requests_obj(resources)

    try:
        unique_name = generate_unique_name(ticket_number)
        resources_path = (
            Terraform.local_terraform_resources_path
            if BaseSetting.debug
            else Terraform.terraform_resources_path
        )
        full_path = resources_path + unique_name
        shutil.copytree(
            src=os.path.join(settings.BASE_DIR, "..", "terraform"), dst=f"{full_path}"
        )
        logger.info(f"Directory {full_path} created ")
        fill_trf_fields(
            policy_name=unique_name,
            data=queue_obj,
            file_path=f"{full_path}/",
            template_name="terf_access.j2",
        )
        tf(working_dir=full_path).init()
        logger.info("Terraform initialized.")

        data = {
            "file_name": unique_name,
            "ticket_number": ticket_number,
            "status": "recived",
            "resource": queue_obj,
        }

        RedisConf.redis_client.lpush(RedisConf.queue_name, str(data))
        logger.info(f"Data: {data} pushed to redis {RedisConf.queue_name} queue")

    except Exception as e:
        logger.error(f"Error at create terraform files cause: {e}")
        raise (e)


@celery_app.task(name="create_tf_files_v2")
def create_tf_files_v2(resources, ticket_number, utm_name):
    logger.info(f"Creating terraform files for ticket {ticket_number}")
    queue_obj = create_requests_obj(resources)
    try:
        unique_name = generate_unique_name(ticket_number)
        resources_path = (
            Terraform.local_terraform_resources_path
            if BaseSetting.debug
            else Terraform.terraform_resources_path
        )
        full_path = resources_path + unique_name
        os.makedirs(f"{full_path}", exist_ok=True)
        # shutil.copytree(src=os.path.join(settings.BASE_DIR,'..','terraform'), dst=f"{full_path}")
        logger.info(f"Directory {full_path} created ")
        with open(f"{full_path}/request.json", "w") as f:
            json.dump(queue_obj, f, indent=2)
        log_file = f"{full_path}/ticket_{ticket_number}.log"
        request_log = logging.getLogger(f"request_{ticket_number}")
        request_log.setLevel(logging.INFO)
        file_handler = logging.FileHandler(filename=log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        request_log.addHandler(file_handler)
        policies = UTMHandler(utm_name).get_policies_from_redis()
        request_log.info("getting policies: done.")
        source = [queue_obj.get("source_name", None)]
        user = [queue_obj.get("user", None)]
        group = [queue_obj.get("group", None)]
        request_log.info(f"source = {source}")
        request_log.info(f"user = {user}")
        request_log.info(f"group = {group}")
        destinations = [queue_obj.get("destination_name", None)]
        request_log.info(f"destination = {destinations}")
        services = [queue_obj.get("service")]
        request_log.info(f"services = {services}")
        matched_policy = filter_utm_policies_services_destination(
            policies=policies, destinations=destinations, services=services
        )
        if matched_policy == []:
            request_log.info(
                "couldn't find any match base on services and destination."
            )
            matched_policy = filter_utm_policies_source_destination(
                policies=policies,
                sources=set(source).union(user, group),
                destinations=destinations
            )
        if matched_policy == []:
            request_log.info(
                "couldn't find any match base on source and destination too."
            )
            fill_trf_fields(
                policy_name=unique_name,
                data=queue_obj,
                file_path=f"{full_path}/",
                template_name="newPolicy.tf.j2",
                utm_name=utm_name,
            )
            request_log.info("created terraform file for create a new policy.")
        else:
            convert_policies_to_terraform_file(
                policies=matched_policy,
                data=queue_obj,
                file_path=f"{Terraform.local_terraform_resources_path if BaseSetting.debug else Terraform.terraform_resources_path}{unique_name}/",
                ticket_number=ticket_number,
            )
            request_log.info("created terraform file for editing the matched policy.")
        tf(working_dir=full_path).init()
        logger.info("Terraform initialized.")
        request_log.info("Terraform initialized.")
        data = {
            "file_name": unique_name,
            "ticket_number": ticket_number,
            "status": "recived",
            "resource": queue_obj,
        }
        try:
            RedisConf.redis_client.lpush(RedisConf.queue_name, str(data))
            logger.info(f"Data: {data} pushed to redis {RedisConf.queue_name} queue")
            request_log.info(
                f"Data: {data} pushed to redis {RedisConf.queue_name} queue"
            )
        except Exception as e:
            logger.info(f"couldnt push to redis: {e}")
            request_log.info(f"couldnt push to redis: {e}")
            raise (e)
    except Exception as e:
        logger.error(f"Error at create terraform files cause: {e}")
        request_log.error(f"Error at create terraform files cause: {e}")
        raise (e)
