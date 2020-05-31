"""Showing status from Slack profile."""
import os
import datetime
import platform
import glob
import time

import util
import util_slack
import util_google


def main(event, context):
    err = 1
    cnt = 0
    slack_stat = ""
    slack_stat_old = ""
    slack_exp_uni = 0
    slack_exp_uni_old = 0
    exp_ch_post_f = False
    main_status = ""
    main_status_old = ""
    pdirname = './'

    while err == 0:
        # Check expire status. If expire within 1min, change status to main_status.
        util_slack.slack_change_main(slack_exp_uni, pdirname, main_status)

        # Get Slack status
        slack_json = util_slack.slack_status_get()
        slack_stat = slack_json['profile']['status_text']
        slack_exp_uni = slack_json['profile']['status_expiration']
        print(slack_stat, slack_exp_uni)

        slack_stat, main_status = util_slack.slack_status_adj(slack_stat, main_status)

        # Check expring and post message.
        exp_ch_post_f = util_slack.slack_exp_check(slack_exp_uni, slack_exp_uni_old, exp_ch_post_f)

        if "At my office" in slack_stat:
            slack_stat = "At my office"

        # Status change check adn post message.
        util_slack.slack_stat_chan_check(pdirname, slack_stat, slack_stat_old, ui_image, slack_exp_uni)
        util_slack.slack_mainstatus_chen_check(main_status, main_status_old)

        # Update parameters.
        time.sleep(20)
        slack_stat_old = slack_stat
        slack_exp_uni_old = slack_exp_uni
        main_status_old = main_status
        err = 0
