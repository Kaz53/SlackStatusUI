"""Showing status from Slack profile."""
import os.path
import cv2
import datetime
import platform
import glob
import time

import util
import util_slack
import util_google
import image_handling


# Main Program
if __name__ == '__main__':
    err = 0
    cnt = 0
    slack_stat = ""
    slack_stat_old = ""
    slack_exp_uni = 0
    slack_exp_uni_old = 0
    exp_ch_post_f = False
    main_status = ""
    main_status_old = ""
    if "arm" in platform.machine():
        os.chdir('/home/pi/Projects/SlackStatusUI')
    pdirname = os.getcwd()


    # Post current time to Slack
    ini_mes = datetime.datetime.now().strftime("%a., %b. %d, %I:%M %p")
    util_slack.post_slack(ini_mes)

    # Loop main program
    while err == 0:
        # Check expire status. If expire within 1min, change status to main_status.
        util_slack.slack_change_main(slack_exp_uni, pdirname, main_status)

        # Get Slack status
        slack_json = util_slack.slack_status_get()
        slack_stat = slack_json['profile']['status_text']
        slack_exp_uni = slack_json['profile']['status_expiration']

        slack_stat, main_status = util_slack.slack_status_adj(slack_stat, main_status)
        img_file, text_str, font_size, text_pos, datestr = image_handling.img_param_set(pdirname, slack_stat)

        # Image creation and showing.
        ui_image = image_handling.create_image(pdirname, img_file, datestr, text_str, font_size, text_pos, slack_exp_uni)
        cv2.imshow("MyStatus", ui_image)
        cv2.waitKey(1)

        # Initial adjustment
        if cnt == 0:
            cv2.waitKey(1000)
            cv2.moveWindow("MyStatus", -3, -30)
            cv2.imshow("MyStatus", ui_image)
            cv2.waitKey(1)

            file_list = glob.glob("./log/*jpg")
            for file in file_list:
                os.remove(file)

            if "arm" in platform.machine():
                util.ip_check(pdirname)

        # Check expring and post message.
        exp_ch_post_f = util_slack.slack_exp_check(slack_exp_uni, slack_exp_uni_old, exp_ch_post_f)

        if "At my office" in slack_stat:
            slack_stat = "At my office"

        # Status change check adn post message.
        util_slack.slack_stat_chan_check(pdirname, slack_stat, slack_stat_old, ui_image, slack_exp_uni)
        util_slack.slack_mainstatus_chen_check(main_status, main_status_old)
        util_slack.slack_mainstatus_chen_check(slack_exp_uni, slack_exp_uni_old)

        # Update parameters.
        time.sleep(60)
        slack_stat_old = slack_stat
        slack_exp_uni_old = slack_exp_uni
        main_status_old = main_status

        cnt += 1
        time_now = datetime.datetime.now()
        hourstr = time_now.strftime("%H")
        minstr = time_now.strftime("%M")
        #if int(hourstr) >= 22 and int(minstr) >= 50:
            #util_google.log_output(pdirname, ui_image, slack_stat, slack_exp_uni)
            #break

cv2.waitKey(10)
cv2.destroyAllWindows()
for i in range(1, 5):
    cv2.waitKey(1)
