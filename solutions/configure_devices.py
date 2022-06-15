import os
import hvac
import pynetbox

VAULT_URL = os.environ.get("VAULT_URL", "http://localhost:8001")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN", "developer_token")

secret_path = "/infra"
device = "netbox"

# Connect to Vault using a bearer token
client = hvac.Client(url=VAULT_URL, token=VAULT_TOKEN)

# Read the latest secret version
secret_version_response = client.secrets.kv.v2.read_secret_version(
    path=f'{secret_path}/{device}'
)

# Get the NetBox URL and token
netbox_url = secret_version_response["data"]["data"]["netbox_url"]
netbox_token = secret_version_response["data"]["data"]["api_token"]

print(f"NetBox URL: {netbox_url}\n"
      f"NetBox token: {netbox_token}")
#
nb = pynetbox.api(netbox_url, token=netbox_token)

wireless_controllers = nb.dcim.devices.filter(role="wlc")

for controller in wireless_controllers:
    print(f"Wireless controller: {controller}")

    mgmt_interface = nb.dcim.interfaces.get(device=controller, mgmt_only=True)

    mgmt_interface_ip = nb.ipam.ip_addresses.get(assigned_object_id=mgmt_interface.id, device=controller)
    print(f"IP: {mgmt_interface_ip}")

    device_secrets = client.secrets.kv.v2.read_secret_version(
        path=f'network/{controller.name}'
    )

    device_username = device_secrets["data"]["data"]["username"]
    device_password = device_secrets["data"]["data"]["password"]
    device_enable = device_secrets["data"]["data"]["enable"]

    print(f"Device username: {device_username}\nDevice password: {device_password}\nEnable secret: {device_enable}\n")