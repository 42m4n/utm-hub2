import hashlib
import logging
import uuid
from datetime import date
from random import randint

from common.conf import UTM
from jinja2 import Environment, FileSystemLoader

from ...lansweeper.utilities import get_lansweeper_data
from .interface import (incoming_interface_clients,
                        incoming_interface_server_to_server,
                        outgoing_interface_clients,
                        outgoing_interface_server_to_server)

logger = logging.getLogger(__name__)


def create_requests_obj(udf_fields):
    mapping_dictionary = {
        "udf_sline_3011": "source_name",
        "udf_sline_3013": "destination_name",
        "udf_pick_3016": "action",
        "udf_pick_3017": "schedule",
        "udf_sline_4201": "source_interface",
        "udf_sline_4202": "destination_interface",
        "udf_sline_4203": "service",
        "udf_sline_4560": "access_type",
        "udf_utm_name": "utm_name"  # udf_utm_name is different. change it with the actual name when it be ready.
    }

    new_object = {}

    for udf_key, new_key in mapping_dictionary.items():
        new_object[new_key] = udf_fields.get(udf_key, "")

    new_object['schedule'] = 'always'
    if new_object['action'] == 'Grant': new_object['action'] = "accept"
    if new_object['action'] == 'Deny': new_object['action'] = "deny"
    if new_object['access_type'] != "Server to Server":
        new_object['source_name'] = "all"
        if new_object['access_type'] == "User to Server":
            new_object['user'] = udf_fields.get('udf_sline_3011').split("@")[0]
        if new_object['access_type'] == "User Group to Server":
            new_object['group'] = udf_fields.get('udf_sline_3011')
    logger.info(f'Queue object {new_object} created. ')
    return new_object


def create_requests_list(udf_fields):
    """
    This code block get raw dictionary of ticket fields and group them by request rows and make list of access requests
    Args:
        udf_fields: dictionary of all access requests fields in a ticket

    Returns:
        requests_list: list of objects that each object has source_name,destination_name,port,action and schedule
    """
    rows = [
        ["udf_sline_3324", "udf_sline_3325", "udf_sline_3326", "udf_sline_3327", "udf_sline_3328", "udf_pick_3329",
         "udf_pick_3330"],

        ["udf_sline_3317", "udf_sline_3318", "udf_sline_3319", "udf_sline_3320", "udf_sline_3321", "udf_pick_3322",
         "udf_pick_3323"],

        ["udf_sline_3310", "udf_sline_3311", "udf_sline_3312", "udf_sline_3313", "udf_sline_3314", "udf_pick_3315",
         "udf_pick_3316"],

        ["udf_sline_3301", "udf_sline_3302", "udf_sline_3303", "udf_sline_3304", "udf_sline_3305", "udf_pick_3306",
         "udf_pick_3307"],
        # server
        ["udf_sline_3025", "udf_sline_3026", "udf_sline_3027", "udf_sline_3028", "udf_sline_3029", "udf_pick_3030",
         "udf_pick_3031", "udf_sline_4207", "udf_sline_4208", "udf_sline_4209"],

        # group
        # udf_sline_3018 : group name
        ["udf_sline_3018", "udf_sline_3019", "udf_sline_3020", "udf_sline_3021", "udf_sline_3022", "udf_pick_3023",
         "udf_pick_3024", "udf_sline_4204", "udf_sline_4205", "udf_sline_4206"],

        # user
        # udf_sline_3011 : user email
        ["udf_sline_3011", "udf_sline_3012", "udf_sline_3013", "udf_sline_3014", "udf_sline_3015", "udf_pick_3016",
         "udf_pick_3017", "udf_sline_4201", "udf_sline_4202", "udf_sline_4203"],
    ]

    requests = [{} for i in range(len(rows))]
    for key in udf_fields.keys():
        for i, row in enumerate(rows):
            if key in row:
                n_key = key

                if key == row[0]:

                    if key == "udf_sline_3011" and udf_fields[key]:
                        n_key = "user"
                        udf_fields[key] = udf_fields[key].split("@")[0]
                        requests[i]["source_name"] = "all"

                    elif key == "udf_sline_3018" and udf_fields[key]:
                        n_key = "group"
                        requests[i]["source_name"] = "all"
                    else:
                        n_key = "source_name"

                if key == row[2]:
                    n_key = "destination_name"
                if key == row[4]:
                    n_key = "port"
                if key == row[5]:
                    n_key = "action"
                if udf_fields[key] == "Grant":
                    udf_fields[key] = "accept"
                elif udf_fields[key] == "Deny":
                    udf_fields[key] = "deny"
                if key == row[6] and udf_fields[key]:
                    n_key = "schedule"
                    udf_fields[key] = udf_fields[key].lower()

                # user
                if key == 'udf_sline_4201':
                    n_key = "source_interface"
                if key == 'udf_sline_4202':
                    n_key = "destination_interface"
                if key == 'udf_sline_4203':
                    n_key = "service"
                # group
                if key == 'udf_sline_4204':
                    n_key = "source_interface"
                if key == 'udf_sline_4205':
                    n_key = "destination_interface"
                if key == 'udf_sline_4206':
                    n_key = "service"

                # server
                if key == 'udf_sline_4207':
                    n_key = "source_interface"
                if key == 'udf_sline_4208':
                    n_key = "destination_interface"
                if key == 'udf_sline_4209':
                    n_key = "service"

                requests[i][n_key] = udf_fields[key]

    requests_list = []
    requests = [d for d in requests if any(value is not None for value in d.values())]
    for item in requests:
        new_object = {
            "group": item.get("group", ""),
            "user": item.get("user", ""),
            "destination_name": item.get("destination_name", ""),
            "source_name": item.get("source_name", ""),
            "action": item.get("action", ""),
            "schedule": (item.get("schedule", "")),
            "destination_interface": item.get("destination_interface", ""),
            "source_interface": item.get("source_interface", ""),
            "service": item.get("service", ""),

        }
        requests_list.append(new_object)
    return requests_list


def generate_unique_name(ticket_number):
    """ This method generate file name
    Args:
        ticket_number (_type_): ticket number

    Returns:
        str: generate folder name with date and ticket number and random int
    """

    today = str(date.today()).replace("-", "_")
    unique_name = f"SDP_{today}_{ticket_number}_{randint(1, 100000)}"
    return unique_name


def fill_trf_fields(policy_name, data, file_path):
    """this method create terraform data with j2

    Args:
        data (json): data
        policy_name (str) : unique policy name
        file_path (str): the path that main.tf file will create
    """
    try:
        services = data.get("service")
        services_list = services.split(',')

        policy_id = generate_uuid()
        file_loader = FileSystemLoader('infra-api/apps/paasapp/templates')
        env = Environment(loader=file_loader)
        template = env.get_template('terf_access.j2')

        dest_ipaddr_json = get_lansweeper_data(data.get('destination_name'), 1)
        dest_ipaddr = dest_ipaddr_json[0]['ip']
        if data.get('access_type') == "Server to Server":
            src_ipaddr_json = get_lansweeper_data(data.get('source_name'), 1)
            src_ipaddr = src_ipaddr_json[0]['ip']
            source_interface = incoming_interface_server_to_server(src_ipaddr)
            destination_interface = outgoing_interface_server_to_server(dest_ipaddr)
        else:
            source_interface = incoming_interface_clients(data.get(
                'source_name').replace("@asax.ir", ""), data.get('utm_name'))
            destination_interface = outgoing_interface_clients(
                dest_ipaddr, data.get('utm_name'))

        trf_file = template.render(
            policy_id=policy_id,
            utm_path=next((_['UTM_ADDRESS'] for _ in UTM.utms if _['UTM_NAME'] == data.get('utm_name')), None),
            utm_token=next((_['UTM_TOKEN'] for _ in UTM.utms if _['UTM_NAME'] == data.get('utm_name')), None),
            policy_name=policy_name,
            source_name=data.get('source_name'),
            destination_name=data.get('destination_name'),
            services=services_list,
            action=data.get('action'),
            schedule=data.get('schedule'),
            source_interface=source_interface,
            destination_interface=destination_interface,
            user=data.get('user'),
            group=data.get('group'),
            access_type=data.get('access_type')

        )

        with open(file_path + "main.tf", 'w') as config:
            logger.info(f'File main.tf created in {file_path} ')
            config.write(trf_file)
            logger.info('Terraform file updated in file_path ')

    except Exception as e:
        logger.error(f'Fill Terraform template failed cause: {e}')
        raise (e)


def decode_utm_token():
    input_token = UTM.utm_token
    input_encoded_token = hashlib.sha256(("2825" + input_token).encode()).hexdigest()
    return input_encoded_token


def generate_uuid():
    new_uuid = str(uuid.uuid4())
    return new_uuid
