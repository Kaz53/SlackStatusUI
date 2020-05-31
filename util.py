import os
import json
import ipget

import util_slack


def load_status_param(pdirname, slack_stat):
    """Load status parameters."""
    status_param_file = os.path.join(pdirname, 'SlackStatus_param.json')
    with open(status_param_file, 'rb') as status_params:
        status_params_json = json.load(status_params)
    img_name = status_params_json[slack_stat]["img_file"]
    text_str = status_params_json[slack_stat]["text_str"]
    x_offset = status_params_json[slack_stat]["pos_x_offset"]
    y_offset = status_params_json[slack_stat]["pos_y_offset"]
    font_size = status_params_json[slack_stat]["font_size"]
    emoji = status_params_json[slack_stat]["emoji"]

    return img_name, text_str, x_offset, y_offset, font_size, emoji

def ip_check(pdirname):
    """IP Address check."""
    ip_addr_prev = ""
    logdir = os.path.join(pdirname, "log")
    ip_file_name = os.path.join(logdir, 'ip.txt')
    if os.path.exists(ip_file_name) is True:
        with open(ip_file_name) as ip_file:
            ip_addr_prev = ip_file.read()

    ip_addr = ipget.ipget().ipaddr("wlan0")

    if ip_addr != ip_addr_prev:
        mes_body = 'New IP Address: ' + ip_addr
        util_slack.post_slack(mes_body)
        with open(ip_file_name, mode='w') as ip_file:
            ip_file.write(ip_addr)