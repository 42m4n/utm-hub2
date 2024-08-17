import logging
import os

from InfraApp.celery import celery_app
from apps.paasapp.modules.terraform import generate_unique_name, fill_trf_fields, create_requests_obj
from common.conf import Redis as RedisConf
from common.conf import Terraform
from django.conf import settings

from common.logger import logger


@celery_app.task(name='create_tf_files')
def create_tf_files(resources, ticket_number):
    logger.info(f'Creating terraform files for ticket {ticket_number}')
    queue_obj = create_requests_obj(resources)

    try:
        unique_name = generate_unique_name(ticket_number)

        if settings.DEBUG:
            os.makedirs(f"{Terraform.terraform_resources_path}{unique_name}", exist_ok=True)
            logger.info(f'Directory {Terraform.terraform_resources_path}{unique_name} created ')

            # ToDo: use shutil for copy
            os.system(f'ln -s {Terraform.terraform_base_path}/.terraform {Terraform.terraform_resources_path}{unique_name}/.terraform')
            os.system(f'ln -s {Terraform.terraform_base_path}/.terraform.lock.hcl {Terraform.terraform_resources_path}{unique_name}/.terraform.lock.hcl')
            logger.info('Terraform base path copied')
            fill_trf_fields(unique_name, queue_obj, f"{Terraform.terraform_resources_path}{unique_name}/")

        data = {
            "file_name": unique_name,
            "ticket_number": ticket_number,
            "status": "recived",
            "resource": queue_obj
        }

        RedisConf.redis_client.lpush(RedisConf.queue_name, str(data))
        logger.info(f'Data: {data} pushed to redis {RedisConf.queue_name} queue')

    except Exception as e:
        logger.error(f'Error at create terraform files cause: {e}')
        raise (e)