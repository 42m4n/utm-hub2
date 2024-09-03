from time import sleep
import re
import os
import logging
from python_terraform import Terraform
from logger import logger

from conf import Redis as RedisConf, Terraform as TerraformConf, BaseSetting, UTM
from send_response import send_response_to_manage_engine


def format_terraform_result(terraform_result):
    try:
        ret_code, out, err = terraform_result
        result_dict = {}
        success = True
        if ret_code == 0:
            output = re.findall(r'Plan: (\d+) to add, (\d+) to change, (\d+) to destroy', out)
            if output:
                result_dict['add'], result_dict['change'], result_dict['destroy'] = map(int, output[0])

        else:
            result_dict['error'] = str(err)
            success = False

        return result_dict, success
    except Exception as e:
        print('Error at format terraform result:')
        print(e)
        logger.error(f'Error at format terraform result {e}')

        raise e


def apply_terraform(queue_object,var_utm_token):
    files_directory = TerraformConf.local_terraform_resources_path if BaseSetting.debug else TerraformConf.terraform_resources_path
    file_location = f'{files_directory}{queue_object["file_name"]}'
    logger.info(f'Applying terraform in {file_location} ')
    log_file = f"{file_location}/ticket_{queue_object['ticket_number']}.log"
    apply_log = logging.getLogger(f"request_{queue_object['ticket_number']}")
    apply_log.setLevel(logging.INFO)
    file_handler = logging.FileHandler(filename=log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    apply_log.addHandler(file_handler)    
    variables = {
    'utm_token': var_utm_token
    }
    tf = Terraform(working_dir=file_location)
    tf.init()
    terraform_result = tf.apply(var=variables,skip_plan=True)
    apply_log.info("terraform applied. stdout is: ...")
    apply_log.info(terraform_result[1])
    apply_log.info("stderr is: ...")
    apply_log.info(terraform_result[2])
    formatted_result, success = format_terraform_result(terraform_result)
    return formatted_result, success


def get_utm_hostname(queue_object):
    files_directory = TerraformConf.local_terraform_resources_path if BaseSetting.debug else TerraformConf.terraform_resources_path
    file_location = f'{files_directory}{queue_object["file_name"]}/provider.tf'
    with open(file_location,"r") as file:
        content = file.read()
    pattern = r'hostname\s*=\s*"([^"]+)"'
    match = re.search(pattern=pattern,string=content)
    if match:
        return match.group(1)
    else:
        return None


def set_utm_token(hostname):
    for utm in UTM.utms:
        if utm.get("UTM_ADDRESS") == hostname:
            token = utm.get("UTM_TOKEN")
            return token


def process_queue():
    logger.info('Start queue process ... ')
    while True:
        try:
            queue_len = RedisConf.redis_client.llen(RedisConf.queue_name)
            if queue_len > 0:
                logger.info(f'Queue count: {queue_len} ')

                _, data = RedisConf.redis_client.brpop(RedisConf.queue_name)
                data = eval(data)
                logger.info(f'Received data from cache: {data}')

                try:
                    utm_token = set_utm_token(get_utm_hostname(data))
                    result, success = apply_terraform(queue_object=data,var_utm_token=utm_token)
                    if success:
                        send_response_to_manage_engine(
                            request_id=data.get('ticket_number'),
                            source=data.get("resource").get("group") or data.get("resource").get("user") or data.get(
                                "resource").get("source_name"),
                            destination=data.get("resource").get("destination_name"),
                            service=data.get("resource").get("service"),
                            response_code="1")
                    else:
                        send_response_to_manage_engine(
                            request_id=data.get('ticket_number'),
                            source=data.get("resource").get("group") or data.get("resource").get("user") or data.get(
                                "resource").get("source_name"),
                            destination=data.get("resource").get("destination_name"),
                            service=data.get("resource").get("service"),
                            response_code="2")

                    logger.info(f"UTM terraform result for {data.get('ticket_number')}: {result}")

                except Exception as error:
                    print(f'Error at apply terraform cause: {error}')
                    logger.error(f'Error at apply terraform cause: {error}')
                    send_response_to_manage_engine(
                        request_id=data.get('ticket_number'),
                        source=data.get("resource").get("group") or data.get("resource").get("user") or data.get(
                            "resource").get("source_name"),
                        destination=data.get("resource").get("destination_name"),
                        service=data.get("resource").get("service"),
                        response_code="2")

                logger.info('Start delay for process queue ...')
                print('Start delay for process queue ...')
                sleep(TerraformConf.delay)

            else:
                print('No requests received ')
                logger.warning('No requests received ')
                sleep(60)

        except Exception as e:
            logger.error(f'Redis connection error: {e}')
            print(f'Redis connection error: {e}')
            sleep(2)


if __name__ == "__main__":
    process_queue()
