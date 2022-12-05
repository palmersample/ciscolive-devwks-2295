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
