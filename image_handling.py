import cv2
import datetime
import numpy as np
import os
import locale

import util

def overlay_icon(background, x, y, icon):
    """Image Overay."""
    hight, width, _ = icon.shape
    background[y:y + hight, x:x + width] = icon

    return background



def create_image(pdirname, img_file, datestr, text_str, font_size, text_pos, slack_exp_uni):
    dirname = os.path.join(pdirname, "data")
    # Logo files load
    PAL_logo_file = os.path.join(dirname, 'FXPAL.png')

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

def img_param_set(pdirname, slack_stat):
    text_pos_x = 200
    text_pos_y = 290
    dirname = os.path.join(pdirname, "data")
    img_name, text_str, x_offset, y_offset, font_size, emoji = \
        util.load_status_param(pdirname, slack_stat)
    img_file = os.path.join(dirname, img_name)
    text_pos = (text_pos_x + x_offset, text_pos_y + y_offset)


    locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
    datestr = datetime.datetime.now().strftime("%a., %b. %d, %I:%M %p")

    return img_file, text_str, font_size, text_pos, datestr