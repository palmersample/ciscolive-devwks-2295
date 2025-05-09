"""
Change IOSXE password using Vault, NetBox, Jinja2, and NETCONF
"""

import os
import hvac
import pynetbox
from ncclient import manager
import ncclient.transport.errors
from helpers import template_env


if __name__ == "__main__":
    print("Loading template... ", end="")
    netconf_password_template = template_env.get_template("change_password.xml.j2")
    print("OK")

    VAULT_URL = os.environ.get("VAULT_URL")
    VAULT_TOKEN = os.environ.get("VAULT_TOKEN")

    secret_path = "/infra"
    device = "netbox"

    # Connect to Vault using a bearer token
    vault = hvac.Client(url=VAULT_URL, token=VAULT_TOKEN)

    print("Retrieving NetBox API token from Vault... ", end="")

    # Read the latest secret version
    netbox_secret = vault.secrets.kv.v2.read_secret_version(
        path=f'{secret_path}/{device}'
    )

    # Extract the NetBox URL and token from the response
    netbox_url = netbox_secret["data"]["data"]["netbox_url"]
    netbox_token = netbox_secret["data"]["data"]["netbox_token"]

    print(f"{netbox_token}\n")

    print("*" * 78)

    netbox = pynetbox.api(url=netbox_url, token=netbox_token)

    for device in netbox.dcim.devices.filter(platform="iosxe",
                                             device_role="router",
                                             cf_workshop_pod_number=os.environ.get("POD_NUMBER")):
        print(f"Processing device {device}...")
        mgmt_interface = netbox.dcim.interfaces.get(device_id=device.id,
                                                    mgmt_only=True)

        mgmt_interface = netbox.ipam.ip_addresses.get(interface_id=mgmt_interface.id)

        device_dns_hostname = mgmt_interface.dns_name
        print(f"\t- Retrieved management interface '{mgmt_interface.assigned_object.name}'")
        print(f"\t- Retrieved hostname '{device_dns_hostname}'")

        device_secret = vault.secrets.kv.v2.read_secret_version(path=f"/network/{device}")
        device_username = device_secret["data"]["data"]["username"]
        device_password = device_secret["data"]["data"]["password"]
        print(f"\t- Retrieved existing credentials: '{device_username} / {device_password}'")

        generated_password = vault.read("sys/policies/password/network/generate")
        new_password = generated_password["data"]["password"]
        print(f"\t- Generated new password: '{new_password}'")

        netconf = manager.connect(host=device_dns_hostname,
                                  username=device_username,
                                  password=device_password,
                                  ssh_config="./netconf_ssh_config")

        # Lock the datastores
        with netconf.locked("running"):
            with netconf.locked("candidate"):
                payload = netconf_password_template.render(username=device_username,
                                                           new_password=new_password)
                netconf.edit_config(target="candidate", config=payload)
                netconf.commit()
                try:
                    manager.connect(host=device_dns_hostname,
                                    username=device_username,
                                    password=new_password,
                                    ssh_config="./netconf_ssh_config")
                except ncclient.transport.errors.AuthenticationError as err:
                    print(f"\t- Password update failed. Reverting to original... {err}")
                    payload = netconf_password_template.render(username=device_username,
                                                               new_password=device_password)
                    netconf.edit_config(target="candidate", config=payload)
                    netconf.commit()
                else:
                    print("\t- Password update successful! Updating Vault...")
                    vault.secrets.kv.v2.create_or_update_secret(path=f"/network/{device}",
                                                                secret={
                                                                    "username": device_username,
                                                                    "password": new_password
                                                                })

        print("*" * 78)
