"""
Helper functions for NETCONF RPC transactions
"""
from jinja2 import Environment, FileSystemLoader, select_autoescape

template_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(),
    lstrip_blocks=True,
    trim_blocks=True
)
