import ipaddress
import logging

import requests
import urllib3
from django.core.cache import cache

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from common.conf import UTM

logger = logging.getLogger(__name__)


class UTMHandler:
    def __init__(self, utm_name):
        self.utm_name = utm_name
        self.utm_token = next(
            (_["UTM_TOKEN"] for _ in UTM.utms if _["UTM_NAME"] == utm_name), None
        )
        self.utm_path = next(
            (_["UTM_ADDRESS"] for _ in UTM.utms if _["UTM_NAME"] == utm_name), None
        )
        self.headers = {
            "Authorization": f"Bearer {self.utm_token}",
            "Content-Type": "application/json",
        }
        self.interfaces_url = f"https://{self.utm_path}/{UTM.utm_interfaces_api}"
        self.services_url = f"https://{self.utm_path}/{UTM.utm_services_api}"
        self.timeout = 20

    def get_services(self, search_field=None):
        cache_key = (
            f"{self.utm_name}_utm_services_{search_field.lower()}"
            if search_field
            else f"{self.utm_name}_utm_services"
        )
        cached_data = None
        try:
            cached_data = cache.get(cache_key)
        except Exception as e:
            logger.warning(f"could not access cache: {e}")
        if cached_data:
            logger.info("Get UTM services from cache")
            return cached_data
        else:
            try:
                logger.info("Get services from UTM")
                response = requests.get(
                    self.services_url,
                    headers=self.headers,
                    verify=False,
                    timeout=self.timeout,
                )
                response = response.json()
                services = response.get("results")
                result = []
                for i, obj in enumerate(services, start=1):
                    new_obj = {"name": obj["name"], "id": i}
                    result.append(new_obj)
                if search_field:
                    result = [
                        i
                        for i in result
                        if i["name"].lower().startswith(search_field.lower())
                        or (
                            len(search_field) >= 3
                            and search_field.lower() in i["name"].lower()
                        )
                    ]
                    try:
                        cache.set(
                            f"{self.utm_name}_utm_services_{search_field}", result
                        )
                    except Exception as e:
                        logger.warning(f"Could not set cache: {e}")
                else:
                    try:
                        cache.set(f"{self.utm_name}_utm_services", result)
                    except Exception as e:
                        logger.warning(f"Could not set cache: {e}")
                return result
            except requests.exceptions.Timeout:
                logger.error(f"Request to {self.utm_name} on {self.utm_path} timed out")
            except Exception as e:
                logger.error(f"Error at getting utm services: {e}")

    def get_interfaces(self, search_field=None):
        cache_key = (
            f"{self.utm_name}_utm_interfaces_{search_field.lower()}"
            if search_field
            else "utm_interfaces"
        )
        cached_data = None
        try:
            cached_data = cache.get(cache_key)
        except Exception as e:
            logger.warning(f"could not access cache: {e}")
        if cached_data:
            logger.info("Get UTM interfaces from cache")
            return cached_data
        else:
            try:
                logger.info("Get interfaces from UTM")
                response = requests.get(
                    self.interfaces_url,
                    headers=self.headers,
                    verify=False,
                    timeout=self.timeout,
                )
                response = response.json()
                services = response.get("results")
                result = [{"name": "any", "id": 1}]
                for i, obj in enumerate(services, start=2):
                    new_obj = {"name": obj["name"], "id": i}
                    result.append(new_obj)
                if search_field:
                    result = [
                        i
                        for i in result
                        if i["name"].lower().startswith(search_field.lower())
                        or (
                            len(search_field) >= 3
                            and search_field.lower() in i["name"].lower()
                        )
                    ]
                    try:
                        cache.set(
                            f"{self.utm_name}_utm_interfaces_{search_field}", result
                        )
                    except Exception as e:
                        logger.warning(f"Could not set cache: {e}")
                else:
                    try:
                        cache.set(f"{self.utm_name}_utm_interfaces", result)
                    except Exception as e:
                        logger.warning(f"Could not set cache: {e}")
                return result
            except requests.exceptions.Timeout:
                logger.error(f"Request to {self.utm_name} on {self.utm_path} timed out")
            except Exception as e:
                logger.error(f"Error at getting utm interfaces: {e}")

    def get_interface_by_ip(self, ip_address):
        cache_key = (
            f"{self.utm_name}_utm_interfaces_{ip_address}"
        )
        cached_data = None
        try:
            cached_data = cache.get(cache_key)
        except Exception as e:
            logger.warning(f"could not access cache: {e}")
        if cached_data:
            logger.info("Get UTM interfaces from cache")
            return cached_data
        else:
            try:
                response = requests.get(
                    self.interfaces_url,
                    headers=self.headers,
                    verify=False,
                    timeout=self.timeout,
                    )
                response = response.json()
                for interface in response.get("results"):
                    int_name = interface.get('name')
                    int_ipaddr, int_netmask = interface.get('ip').split()
                    int_cidr = sum(
                        bin(int(x)).count('1') for x in int_netmask.split('.'))
                    int_network = ipaddress.ip_network(
                        f"{int_ipaddr}/{int_cidr}", strict=False)
                    if ip_address in int_network:
                        return int_name
                return None
            except Exception as e:
                logger.error(f'Error at getting interface by IP: {e}')
                return None
