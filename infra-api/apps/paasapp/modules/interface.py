import ipaddress

from .ldap import LDAPHandler
from .utm import UTMHandler


def incoming_interface_clients(username, utm_name=None):
    try:
        ldap_handler = LDAPHandler()
        ldap_handler.connect()
        interface = ldap_handler.get_user_ou(username) or "any"
        ldap_handler.disconnect()
    except:
        interface = "any"
    if interface == "Ams":
        return "Ams-teh"
    if interface == "Operations":
        return "Op-support"
    if utm_name == "UTM-Karaj":
        interface = "Lan Client"
    elif utm_name == "UTM-Negar" and interface == "MDP":
        interface = "BI-Client"
    return interface


def outgoing_interface_clients(ipaddr, utm_name=None):
    if utm_name == "UTM-Karaj" or utm_name == "UTM-Negar":
        return "SDWAN-Farhang"
    try:
        ip = ipaddress.IPv4Address(ipaddr)
    except ValueError:
        print(f"Invalid IPv4 address: {ipaddr}")
        return None
    networks = {
        "172.20.0.0/16": "IDC-Farhang",
        "172.28.0.0/16": "SDWAN-Shatel",
        "192.168.0.0/16": "SDWAN-Tebyan",
        "172.31.0.0/16": "SDWAN-Milad",
    }
    # TODO get the neworks from os variables
    for network, interface in networks.items():
        if ip in ipaddress.ip_network(network):
            return interface
    return "any"


def incoming_interface_server_to_server(ipaddr):
    try:
        ip = ipaddress.IPv4Address(ipaddr)
    except ValueError:
        print(f"Invalid IPv4 address: {ipaddr}")
        return None
    utm_handler = UTMHandler()
    try:
        interface = utm_handler.get_interface_by_ip(ip)
    except:
        interface = "any"
    return interface


def outgoing_interface_server_to_server(ipaddr):
    try:
        ip = ipaddress.IPv4Address(ipaddr)
    except ValueError:
        print(f"Invalid IPv4 address: {ipaddr}")
        return None
    networks = {
        "172.28.0.0/16": "SDWAN-Shatel",
        "192.168.0.0/16": "SDWAN-Tebyan",
        "172.31.0.0/16": "SDWAN-Milad",
    }
    for network in list(networks.keys()):
        if ip in ipaddress.ip_network(network):
            return "IDC-Farhang1"
    return incoming_interface_server_to_server(ip)
    # TODO get the neworks from os variables
