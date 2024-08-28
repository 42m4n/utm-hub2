import json
import subprocess
from time import sleep

from conf import Terraform, BaseSetting
from send_response import send_response_to_manage_engine


def remove_lines_from_file(file_name, num_lines):
    try:
        with open(file_name, 'r') as file:
            lines = file.readlines()

        if num_lines >= len(lines):
            # If num_lines is greater than or equal to the total number of lines in the file,
            # just truncate the file to an empty file.
            with open(file_name, 'w') as file:
                file.truncate(0)
        else:
            # Remove the specified number of lines from the beginning of the file.
            with open(file_name, 'w') as file:
                file.writelines(lines[num_lines:])

    except FileNotFoundError:
        print(f"File '{file_name}' not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def process_quese():
    """This method check que to apply the terraform files
    """
    while True:
        queue_file = Terraform.local_terraform_queue_path if BaseSetting.debug else Terraform.terraform_queue_path
        logs_file = Terraform.local_terraform_log_path if BaseSetting.debug else Terraform.terraform_log_path
        files_directory = Terraform.local_terraform_resources_path if BaseSetting.debug else Terraform.terraform_resources_path
        with open(f"{queue_file}", encoding="UTF-8") as whole_queue:
            loaded_lines = 0

            for line in whole_queue:
                loaded_lines += 1
                try:
                    json_line = json.loads(line)
                    file_location = f'{files_directory}{json_line["file_name"]}'

                    terraform_command = f"cd {file_location} && sudo terraform apply -auto-approve"
                    terraform_command_state = subprocess.check_output(terraform_command, text=True, shell=True)

                    with open(f"{logs_file}", "a") as log_file:

                        if "Apply complete!" in terraform_command_state:
                            log_file.write(line + "    Done")
                            send_response_to_manage_engine(
                                request_id=json_line["ticket_number"],
                                source=json_line["resource"]["group"] or json_line["resource"]["user"] or json_line["resource"]["source_name"],
                                destination=json_line["resource"]["destination_name"],
                                service=json_line["resource"]["service"],
                                response_code="1")

                    sleep(Terraform.delay)

                except Exception as es:
                    print(">>>")
                    print(es)
                    with open(f"{logs_file}", "a") as log_file:
                        log_file.write(line + f"Error cause: {es}")

                    send_response_to_manage_engine(
                        request_id=json_line["ticket_number"],
                        source=json_line["resource"]["source_name"],
                        destination=json_line["resource"]["destination_name"],
                        service=json_line["resource"]["service"],
                        response_code="2")
                    pass

        remove_lines_from_file(f"{queue_file}", loaded_lines)


if __name__ == "__main__":
    process_quese()
