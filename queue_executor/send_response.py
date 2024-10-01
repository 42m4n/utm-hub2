import conf
import requests
import urllib3
from logger import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RESPONSE_CODE = {
    "1": "OK",
    "2": "NOT OK"
}


def send_response_to_manage_engine(request_id, response_code, source=None, destination=None, service=None):
    """
    This function update ticket in Manage Engine by add a note to ticket contains
    the result of utm and if the response code is ok change the ticket status to close.
    """

    ticket_url = (
        f"{conf.ManageEngine.manage_engine_address}/api/v3/requests/{request_id}"
    )
    comment_url = f"{ticket_url}/notes"
    headers = {"authtoken": f"{conf.ManageEngine.manage_engine_token}"}

    message = f"source:{source} -> destination:{destination} port:{service} status: {RESPONSE_CODE.get(response_code)}"

    comment_input_data = {
        "note": {
            "description": message,
            "show_to_requester": True,
            "mark_first_response": False,
            "add_to_linked_requests": True,
        }
    }
    status_done_input_data = {
        "request": {"status": {"id": conf.ManageEngine.manage_engine_done_status}}
    }
    status_error_input_data = {
        "request": {"status": {"id": conf.ManageEngine.manage_engine_error_status}}
    }
    comment_data = {"input_data": str(comment_input_data)}
    status_done_data = {"input_data": str(status_done_input_data)}
    status_error_data = {"input_data": str(status_error_input_data)}
    try:
        if response_code == "1":
            logger.info(
                f"Sending data : {comment_input_data} to ManageEngine to add comment"
            )
            response_comment = requests.post(
                comment_url, headers=headers, data=comment_data, verify=False
            )
            logger.info(f"ManageEngine response status: {response_comment.status_code} ")
            response_comment.raise_for_status()
            logger.info(f"ManageEngine comment response: {response_comment.text} ")
            logger.info(
                f"Sending data : {status_done_data} to ManageEngine to change ticket status"
            )
            response = requests.put(
                ticket_url, headers=headers, data=status_done_data, verify=False
            )
            logger.info(f"ManageEngine response for status: {response.status_code} ")
            response.raise_for_status()
            logger.info(f"ManageEngine response: {response.text} ")
        elif response_code == "2":
            logger.info(
                f"Sending data : {status_error_data} to ManageEngine to change ticket status"
            )
            response = requests.put(
                ticket_url, headers=headers, data=status_error_input_data, verify=False
            )
            logger.info(f"ManageEngine response for status: {response.status_code} ")
            response.raise_for_status()
            logger.info(f"ManageEngine response: {response.text} ")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send response to ManageEngine cause: {e}")
