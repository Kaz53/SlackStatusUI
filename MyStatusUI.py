"""Showing status from Slack profile."""
import os.path
import cv2
import datetime
import platform
import numpy as np
import glob
import time
import json
import ipget
import locale

import util
import util_slack
import util_google


def overlay_icon(background, x, y, icon):
    """Image Overay."""
    hight, width, _ = icon.shape
    background[y:y + hight, x:x + width] = icon

    return background

def ip_check():
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


def create_image(PAL_logo_file, img_file, datestr, text_str, text_pos, slack_exp_uni):
    # Overlay Company Logo
    background = np.zeros(shape=(480, 810, 3), dtype=np.uint8)
    background[:, :, 0] = 33
    background[:, :, 1] = 24
    background[:, :, 2] = 22
    background[:120, :, 0] = 137
    background[:120, :, 1] = 112
    background[:120, :, 2] = 107
    background[410:, :, 0] = 137
    background[410:, :, 1] = 112
    background[410:, :, 2] = 107
    icon = cv2.imread(PAL_logo_file)
    overlay_icon(background, 30, 10, icon)

    # Write Title on image
    ui_image = cv2.putText(
        background, "Kazu's status", (150, 70),
        cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
        2.5, (222, 212, 210), 3, cv2.LINE_AA)

    # Write Titile on image
    ui_image = cv2.putText(
        ui_image, "from Slack", (570, 110),
        cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
        1, (209, 172, 145), 2, cv2.LINE_AA)

    # Overlay Emoji ICON
    icon = cv2.imread(img_file)
    overlay_icon(background, 30, 140, icon)

    # Write Current time on image
    ui_image = cv2.putText(
        ui_image, datestr, (450, 450),
        cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
        0.8, (209, 172, 145), 1, cv2.LINE_AA)

    # Write Status on image
    ui_image = cv2.putText(
        ui_image, text_str, text_pos,
        cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
        font_size, (209, 200, 198), 5, cv2.LINE_AA)

    # Write end time
    if text_str in [
        'Meeting', 'Out of office',
        'At FXGI', 'Absence',
        'Working remotely', 'Trip']:
        if slack_exp_uni != 0:
            slack_exp = datetime.datetime.fromtimestamp(slack_exp_uni)
            slack_end = slack_exp.strftime("~%I:%M %p")
            ui_image = cv2.putText(
                ui_image, slack_end, (400, 370),
                cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
                2, (222, 212, 210), 3, cv2.LINE_AA)
    return ui_image


# Main Program
if __name__ == '__main__':
    err = 0
    cnt = 0
    slack_stat = ""
    slack_stat_old = ""
    slack_exp_uni = 0
    slack_exp_uni_old = 0
    exp_ch_post = False
    if "arm" in platform.machine():
        os.chdir('/home/pi/Projects/SlackStatusUI')
    pdirname = os.getcwd()
    dirname = os.path.join(pdirname, "data")
    main_status = ""
    main_status_old = ""

    # Logo files load
    PAL_logo_file = os.path.join(dirname, 'FXPAL.png')

    # Post current time to Slack
    ini_mes = datetime.datetime.now().strftime("%a., %b. %d, %I:%M %p")
    util_slack.post_slack(ini_mes)

    # Loop main program
    while err == 0:
        img_file = ""

        # Check expire status
        if slack_exp_uni != 0:
            now_unix = int(datetime.datetime.now().strftime('%s'))
            diff_unix = slack_exp_uni - now_unix
            # Change status to main_status if expire within 60sec
            if diff_unix <= 60 and main_status != "":
                _, _, _, _, _, emoji = util.load_status_param(pdirname, main_status)
                util_slack.slack_st_chan(
                    main_status, emoji)
                time.sleep(5)

        slack_res_str = util_slack.slack_status_get()
        try:
            slack_json = slack_res_str.json()
        except json.decoder.JSONDecodeError:
            slack_status_str = util_slack.slack_status_get()
            slack_json = slack_res_str.json()
        slack_stat = slack_json['profile']['status_text']

        # slack_stat = '通話中'
        text_pos_x = 200
        text_pos_y = 290
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

        img_name, text_str, x_offset, y_offset, font_size, emoji = \
            util.load_status_param(pdirname, slack_stat)
        img_file = os.path.join(dirname, img_name)
        text_pos = (text_pos_x + x_offset, text_pos_y + y_offset)

        if "At my office" in slack_stat:
            slack_stat = "At my office"

        slack_exp_uni = slack_json['profile']['status_expiration']
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        datestr = datetime.datetime.now().strftime("%a., %b. %d, %I:%M %p")

        # Image creation and showing.
        ui_image = create_image(PAL_logo_file, img_file, datestr, text_str, text_pos, slack_exp_uni)
        cv2.imshow("MyStatus", ui_image)
        cv2.waitKey(1)

        # Initial image position adjustment
        if cnt == 0:
            cv2.waitKey(1000)
            cv2.moveWindow("MyStatus", -3, -30)
            cv2.imshow("MyStatus", ui_image)
            cv2.waitKey(1)

            file_list = glob.glob("./log/*jpg")
            for file in file_list:
                os.remove(file)

            if "arm" in platform.machine():
                ip_check()

        # Check expire soon
        if slack_exp_uni != slack_exp_uni_old:
            exp_ch_post = False
        if exp_ch_post is False and slack_exp_uni != 0:
            exp_ch_post = util.exp_check(slack_exp_uni)

        # Write image and log for history when change status
        if slack_stat != slack_stat_old:
            exp_ch_post = False
            util_google.log_output(pdirname, ui_image, slack_stat, slack_exp_uni)
            mes_body = "Changed to [" + slack_stat + "] from ["\
                + slack_stat_old + "]"
            util_slack.post_slack(mes_body)

        # Post slack when change main status
        if main_status != main_status_old:
            mes_body = "Changed main_status to [" + main_status + "] from ["\
                + main_status_old + "]"
            util_slack.post_slack(mes_body)

        # Wait 20sec
        time.sleep(20)
        slack_stat_old = slack_stat
        slack_exp_uni_old = slack_exp_uni
        main_status_old = main_status

        cnt += 1
        time_now = datetime.datetime.now()
        hourstr = time_now.strftime("%H")
        minstr = time_now.strftime("%M")
        if int(hourstr) >= 22 and int(minstr) >= 50:
            util_google.log_output(pdirname, ui_image, slack_stat, slack_exp_uni)
            break

cv2.waitKey(10)
cv2.destroyAllWindows()
for i in range(1, 5):
    cv2.waitKey(1)
