import ipaddress
import json

import requests
import urllib3
from common.conf import UTM
from common.logger import logger
from django.core.cache import cache

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# logger = logging.getLogger(__name__)


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
        self.policies_url = f"https://{self.utm_path}{UTM.utm_policies_api}"
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
                    url=self.services_url,
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
                    cache.set(cache_key, result)
                except Exception as e:
                    logger.warning(f"Could not set cache: {e}")
                return result
            except requests.exceptions.Timeout:
                logger.error(f"Request to {self.utm_name} on {self.utm_path} timed out")
            except Exception as e:
                logger.error(f"Error at getting utm services: {e}")

    def get_interfaces(self, search_field=None, vdom="root"):
        cache_key = (
            f"{self.utm_name}_{vdom}_utm_interfaces_{search_field.lower()}"
            if search_field
            else f"{self.utm_name}_{vdom}_utm_interfaces"
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
                    url=f"{self.interfaces_url}?vdom={vdom}",
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
                    cache.set(cache_key, result)
                except Exception as e:
                    logger.warning(f"Could not set cache: {e}")
                return result
            except requests.exceptions.Timeout:
                logger.error(f"Request to {self.utm_name} on {self.utm_path} timed out")
            except Exception as e:
                logger.error(f"Error at getting utm interfaces: {e}")

    def get_interface_by_ip(self, ip_address, vdom="root"):
        cache_key = f"{self.utm_name}_utm_interfaces_{vdom}_{ip_address}"
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
                    url=f"{self.interfaces_url}?vdom={vdom}",
                    headers=self.headers,
                    verify=False,
                    timeout=self.timeout,
                )
                response = response.json()
                for interface in response.get("results"):
                    int_name = interface.get("name")
                    int_ipaddr, int_netmask = interface.get("ip").split()
                    int_cidr = sum(
                        bin(int(x)).count("1") for x in int_netmask.split(".")
                    )
                    int_network = ipaddress.ip_network(
                        f"{int_ipaddr}/{int_cidr}", strict=False
                    )
                    if ip_address in int_network:
                        try:
                            cache.set(cache_key, int_name)
                        except Exception as e:
                            logger.warning(f"Could not set cache: {e}")
                        return int_name
                return None
            except Exception as e:
                logger.error(f"Error at getting interface by IP: {e}")
                return None

    def get_policies_from_utm(self):
        """Fetch firewall policies from Fortigate API."""
        try:
            response = requests.get(
                self.policies_url, headers=self.headers, verify=False
            )
            response.raise_for_status()  # Raises an HTTPError for bad responses
            return response.json()["results"]
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 401:
                logger.error(f"Unauthorized access to {self.utm_name} !!!!")
            elif http_err.response.status_code == 429:
                logger.warning(f"Rate limit exceeded for {self.utm_name} !!!!")
            else:
                logger.error(f"HTTP Error: {http_err}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def get_policies_from_redis(self):
        """Fetch firewall policies from Redis."""
        try:
            redis_key = f"{self.utm_name}_policies"
            policies = json.loads(cache.get(redis_key) or b"[]")
            if not policies:
                logger.info("No policies found in Redis. Fetching from UTM...")
                policies = self.get_policies_from_utm()
                cache.set(redis_key, json.dumps(policies))
                logger.info("Policies fetched and stored in Redis successfully")
            logger.info("Policies fetched successfully.")
            return policies
        except Exception as e:
            logger.info("Error fetching policies: ")
            raise (e)


def filter_utm_policies_source_destination(
    policies: list, sources: list, destinations: list
):
    matching_policies = []
    for policy in policies:
        # Get all destination names from the policy
        policy_destinations = set(dst.get("name") for dst in policy.get("dstaddr", []))
        # Get all sources from the policy
        policy_sources = set(src.get("name") for src in policy.get("srcaddr", []))
        # Get all users from the policy
        policy_users = set(user.get("name") for user in policy.get("users", []))
        # Get all groups from the policy
        policy_groups = set(group.get("name") for group in policy.get("groups", []))
        # Check if destinations match exactly
        dst_match = set(destinations) == policy_destinations
        # Check if services match exactly
        sources_match = set(sources) == (policy_sources | policy_users | policy_groups)
        # Check if both destinations and services match exactly
        if dst_match and sources_match:
            matching_policies.append(policy)
    return matching_policies


def filter_utm_policies_services_destination(
    policies: list, services: list, destinations: list
):
    matching_policies = []
    for policy in policies:
        # Get all destination names from the policy
        policy_destinations = set(dst.get("name") for dst in policy.get("dstaddr", []))
        # Get all service names from the policy
        policy_services = set(svc.get("name") for svc in policy.get("service", []))
        # Check if destinations match exactly
        dst_match = set(destinations) == policy_destinations
        # Check if services match exactly
        service_match = set(services) == policy_services
        # Check if both destinations and services match exactly
        if dst_match and service_match:
            matching_policies.append(policy)
    return matching_policies
