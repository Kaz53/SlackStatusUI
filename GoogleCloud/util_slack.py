import os
import requests
import json
import time
import slackweb
import platform
import datetime

import util
import util_google

pdirname = './'

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
        time.sleep(10)
        try:
            slack_res_str = requests.get(
                slack_url_get, params=data, timeout=timeout_time)
        except requests.exceptions.RequestException:
            time.sleep(10)
            try:
                slack_res_str = requests.get(
                    slack_url_get, params=data, timeout=timeout_time)
            except requests.exceptions.RequestException:
                time.sleep(20)
                post_slack("[Error!] Can't get slack status!")
                slack_res_str = ''
            else:
                post_slack("Success to retry getting Slack status.")
        else:
            post_slack("Success to retry getting Slack status.")

    try:
        slack_json = slack_res_str.json()
    except json.decoder.JSONDecodeError:
        slack_res_str = slack_status_get()
        slack_json = slack_res_str.json()

    return slack_json

def slack_change_main(slack_exp_uni, pdirname, main_status):
    # Check expire status. If expire within 1min, change status to main_status.
    if slack_exp_uni != 0:
        now_unix = int(datetime.datetime.now().strftime('%s'))
        diff_unix = slack_exp_uni - now_unix
        # Change status to main_status if expire within 60sec
        if diff_unix <= 120 and main_status != "":
            _, _, _, _, _, emoji = util.load_status_param(pdirname, main_status)
            slack_st_chan(
                main_status, emoji)
            time.sleep(5)

def exp_check(slack_exp_uni):
    """Check exp soon."""
    now_unix = int(datetime.datetime.now().strftime('%s'))
    diff_unix = slack_exp_uni - now_unix
    if diff_unix // 60 <= 5:
        mes_body = "Within 5min, Slack Status will be expired."
        post_slack(mes_body)
    return(diff_unix // 60 <= 5)

def slack_exp_check(slack_exp_uni, slack_exp_uni_old, exp_ch_post_f):
    # Check expire soon
    if slack_exp_uni != slack_exp_uni_old:
        exp_ch_post_f = False
    if exp_ch_post_f is False and slack_exp_uni != 0:
        exp_ch_post_f = exp_check(slack_exp_uni)

    return exp_ch_post_f

def slack_stat_chan_check(pdirname, slack_stat, slack_stat_old, ui_image, slack_exp_uni):
    # Write image and log for history when change status
    if slack_stat != slack_stat_old:
        exp_ch_post = False
        util_google.log_output(pdirname, ui_image, slack_stat, slack_exp_uni)
        mes_body = "Changed to [" + slack_stat + "] from [" \
                   + slack_stat_old + "]"
        post_slack(mes_body)

def slack_mainstatus_chen_check(main_status, main_status_old):
    # Post slack when change main status
    if main_status != main_status_old:
        mes_body = "Changed main_status to [" + main_status + "] from [" \
                   + main_status_old + "]"
        post_slack(mes_body)

def greet_word():
    """Decide greeting word based on time."""
    time_now = datetime.datetime.now()
    time_hour = int(time_now.strftime("%-H"))
    morning_hours = [6, 7, 8, 9]
    evening_hours = [17, 18, 19, 20, 21, 22, 23]

    if time_hour in morning_hours:
        return "At my office1"
    elif time_hour in evening_hours:
        return "At my office2"
    else:
        return "At my office3"


def slack_status_adj(slack_stat, main_status):
    # Parameter adjstments
    # slack_stat = '通話中'
    if slack_stat == "":
        slack_stat = 'Home'
        main_status = ""
    elif slack_stat == 'At work':
        main_status = slack_stat
    elif slack_stat == 'At my office':
        slack_stat = greet_word()
        main_status = slack_stat
    elif slack_stat == '通勤途中':
        slack_stat = 'Commuting'
    elif slack_stat in ['In a meeting', '会議中']:
        if slack_stat == '会議中':
            slack_stat = 'In a meeting'
    elif slack_stat in ['Working remotely', 'リモートで作業中']:
        if slack_stat == 'リモートで作業中':
            slack_stat == 'Working remotely'
        main_status = slack_stat
    elif slack_stat == '病欠':
        slack_stat = 'Absence'
    elif slack_stat == '通話中':
        slack_stat = 'On a call'

    return slack_stat, main_status
