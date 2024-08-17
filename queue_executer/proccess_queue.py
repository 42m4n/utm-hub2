from time import sleep
import re
from python_terraform import Terraform
from logger import logger

from conf import Redis as RedisConf, Terraform as TerraformConf, BaseSetting
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


def apply_terraform(queue_object):
    files_directory = TerraformConf.loca_terraform_resources_path if BaseSetting.debug else TerraformConf.terraform_resources_path
    file_location = f'{files_directory}{queue_object["file_name"]}'
    logger.info(f'Applying terraform in {file_location} ')

    tf = Terraform(working_dir=file_location)
    terraform_result = tf.apply(skip_plan=True)
    formatted_result, success = format_terraform_result(terraform_result)
    return formatted_result, success


def process_queue():
    logger.info('Start queue process ... ')
    print('Start queue process ... ')
    while True:
        try:
            queue_len = RedisConf.redis_client.llen(RedisConf.queue_name)
            if queue_len > 0:
                logger.info(f'Queue count: {queue_len} ')
                print(f'Queue count: {queue_len} ')

                _, data = RedisConf.redis_client.brpop(RedisConf.queue_name)
                data = eval(data)
                logger.info(f'Received data from cache: {data}')
                print(f'Queue object from cache: {data}')

                try:
                    result, success = apply_terraform(data)
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
