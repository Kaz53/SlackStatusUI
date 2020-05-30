import os
import requests
import json
import time
import slackweb
import platform

# Common settings
if "arm" in platform.machine():
    os.chdir('/home/pi/Projects/SlackStatusUI')
pdirname = os.getcwd()

# Slack Seetings
Slack_conf_file = os.path.join(pdirname, 'Slack_conf.json')
with open(Slack_conf_file, 'rb') as Slack_conf:
    Slack_conf_json = json.load(Slack_conf)
Slack_USER_TOKEN = Slack_conf_json['Slack_USER_TOKEN']
Slack_USER_ID = Slack_conf_json['Slack_USER_ID']
slack_kazu_url = Slack_conf_json['Slack_Kazu_channel']
slack_url_get = "https://slack.com/api/users.profile.get"
slack_url_set = "https://slack.com/api/users.profile.set"
timeout_time = (3.0, 7.5)
data = {"token": Slack_USER_TOKEN, "user": Slack_USER_ID}


def post_slack(mes_body):
    """Post message in Kazu channel."""
    slack = slackweb.Slack(url=slack_kazu_url)
    body = mes_body
    slack.notify(text=body)


def slack_st_chan(slack_stat, emoji):
    """Change Slack status."""
    profile = {
        "status_text": slack_stat,
        "status_emoji": emoji,
        "status_expiration": 0}
    profile = json.dumps(profile)
    data["profile"] = profile
    requests.post(slack_url_set, data=data, timeout=timeout_time)

def slack_status_get():
    """Getting status from Slack"""
    # Get current slack status
    try:
        slack_res_str = requests.get(
            slack_url_get, params=data, timeout=timeout_time)
    except requests.exceptions.RequestException:
        time.sleep(30)
        try:
            slack_res_str = requests.get(
                slack_url_get, params=data, timeout=timeout_time)
        except requests.exceptions.RequestException:
            time.sleep(60)
            try:
                slack_res_str = requests.get(
                    slack_url_get, params=data, timeout=timeout_time)
            except requests.exceptions.RequestException:
                time.sleep(60)
                post_slack("[Error!] Can't get slack status!")
                slack_res_str = ''
            else:
                post_slack("Success to retry getting Slack status.")
        else:
            post_slack("Success to retry getting Slack status.")
    return slack_res_str
