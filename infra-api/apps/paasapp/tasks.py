import os
import shutil

from InfraApp.celery import celery_app
from python_terraform import Terraform as tf
from apps.paasapp.modules.terraform import generate_unique_name, fill_trf_fields, create_requests_obj
from common.conf import Redis as RedisConf
from common.conf import Terraform, BaseSetting
from django.conf import settings
from common.logger import logger
from .modules.terraform import convert_policies_to_terraform_file
from .modules.utm import UTMHandler,filter_utm_policies_source_destination,filter_utm_policies_services_destination


@celery_app.task(name='create_tf_files')
def create_tf_files(resources, ticket_number):
    logger.info(f'Creating terraform files for ticket {ticket_number}')
    queue_obj = create_requests_obj(resources)

    try:
        unique_name = generate_unique_name(ticket_number)
        resources_path = Terraform.local_terraform_resources_path if BaseSetting.debug else Terraform.terraform_resources_path
        full_path = resources_path + unique_name
        shutil.copytree(src=os.path.join(settings.BASE_DIR,'..','terraform'), dst=f"{full_path}")
        logger.info(f'Directory {full_path} created ')
        fill_trf_fields(policy_name=unique_name, data=queue_obj, file_path=f"{full_path}/", template_name="terf_access.j2")
        tf(working_dir=full_path).init()
        logger.info('Terraform initialized.')

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

@celery_app.task(name='create_tf_files_v2')
def create_tf_files_v2(resources, ticket_number,utm_name):
    logger.info(f'Creating terraform files for ticket {ticket_number}')
    queue_obj = create_requests_obj(resources)
    try:
        unique_name = generate_unique_name(ticket_number)
        resources_path = Terraform.local_terraform_resources_path if BaseSetting.debug else Terraform.terraform_resources_path
        full_path = resources_path + unique_name
        os.makedirs(f"{full_path}", exist_ok=True)
        # shutil.copytree(src=os.path.join(settings.BASE_DIR,'..','terraform'), dst=f"{full_path}")
        logger.info(f'Directory {full_path} created ')
        policies = UTMHandler(utm_name).get_policies()
        sources = [queue_obj.get("source_name")]
        destinations = [queue_obj.get("destination_name")]
        services = [queue_obj.get("service")]
        matched_policy = filter_utm_policies_services_destination(policies=policies,destinations=destinations,services=services)
        if matched_policy == []:
            matched_policy = filter_utm_policies_source_destination(policies=policies,sources=sources,destinations=destinations)
        if matched_policy == []:
            fill_trf_fields(policy_name=unique_name,data=queue_obj,file_path=f"{full_path}/",template_name="newPolicy.tf.j2")
        if matched_policy != []:
            convert_policies_to_terraform_file( policies=matched_policy,
                                                data=queue_obj,
                                                file_path=f"{Terraform.local_terraform_resources_path 
                                                            if BaseSetting.debug else Terraform.terraform_resources_path}{unique_name}/",
                                                ticket_number=ticket_number)
        tf(working_dir=full_path).init()
        logger.info('Terraform initialized.')
        data = {
            "file_name": unique_name,
            "ticket_number": ticket_number,
            "status": "recived",
            "resource": queue_obj
        }
        try:
            RedisConf.redis_client.lpush(RedisConf.queue_name, str(data))
            logger.info(f'Data: {data} pushed to redis {RedisConf.queue_name} queue')
        except Exception as e:
            logger.info(f"couldnt push to redis: {e}")
            raise(e)
    except Exception as e:
        logger.error(f'Error at create terraform files cause: {e}')
        raise(e)