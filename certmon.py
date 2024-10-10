import argparse
import ssl
import socket
import time
import requests
import yaml
from math import floor
import OpenSSL
from pprint import pprint
from datetime import datetime


def get_certificate(host, port=443, timeout=10):
    context = ssl.create_default_context()
    conn = socket.create_connection((host, port))
    sock = context.wrap_socket(conn, server_hostname=host)
    sock.settimeout(timeout)
    try:
        der_cert = sock.getpeercert(True)
    finally:
        sock.close()
    return ssl.DER_cert_to_PEM_cert(der_cert)


def get_cert_metrics(host, port=443, timeout=10):
    certificate = get_certificate(host)
    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, certificate)

    days_left = floor((datetime.strptime(x509.get_notAfter().decode(), '%Y%m%d%H%M%SZ').timestamp() - time.time()) / 86400)
    subject = ""
    for part in x509.get_subject().get_components():
        subject += "/" + part[0].decode() + "=" + part[1].decode()

    return {
        "subject": subject, 
        "days_left": days_left
    }

def check_result(result):
    if not result.status_code in (200, 201):
        raise Exception(f"{result.status_code} - {result.content}")
    return result

parser = argparse.ArgumentParser(
                    prog='certmon',
                    description='Monitors certs and expirations')
parser.add_argument('-c', '--config')      # option that takes a value
args = parser.parse_args()
if args.config is None:
    parser.print_usage()
    exit(1)

with open(args.config, "r") as f:
    config = yaml.safe_load(f)

print(config)

ops_url = f"https://{config['ops_host']}/suite-api/api"

headers = { "Content-Type": "application/json", "Accept": "application/json" }


payload = {
    "username": config["ops_username"],
    "password": config["ops_password"],
    "authSource": config["ops_auth_source"],
}

result = requests.post(ops_url + "/auth/token/acquire", json=payload, verify=False, headers=headers)
check_result(result)
token = result.json()["token"]
headers["Authorization"] = "OpsToken " + token

adapterKindKey = "CustomCertificateAdapter"
resourceKindKey = "CustomCertificate"

for url  in config["sites"]:
    cert_metrics = get_cert_metrics(url);
    payload = {
        "name": [ cert_metrics["subject"] ]
    }

    # Find or create resource corresponding to subject
    result = requests.post(ops_url + "/resources/query", json=payload, verify=False, headers=headers)
    check_result(result)
    resources = result.json()["resourceList"]
    if len(resources) == 0:
        # Not found. Create resource
        payload = {
            "adapterKindKey": adapterKindKey,
            "resourceKindKey": resourceKindKey,
            "resourceKey": {
                "name": cert_metrics["subject"],
                "adapterKindKey": adapterKindKey,
                "resourceKindKey": resourceKindKey
            }
        }
        result = requests.post(ops_url + "/resources/adapterkinds/" + adapterKindKey, json=payload, verify=False, headers=headers)
        check_result(result)
        resourceId = result.json()["identifier"]
    else:
        resourceId = resources[0]["identifier"]
    print(resourceId)

    # Submit metrics
    payload  = {
        "resource-stat-content" : [ {
            "id" : resourceId,
            "stat-contents" : [ {
                "statKey" : "daysToExpiry",
                "timestamps" : [ int(time.time()) * 1000 ],
                "data" : [ cert_metrics["days_left"] ]
            } ]
        }]
    }
    result = requests.post(ops_url + "/resources/stats", json=payload, verify=False, headers=headers)
    check_result(result)


