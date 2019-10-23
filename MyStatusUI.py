"""Showing status from Slack profile."""
import requests
import os.path
import cv2
import datetime
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import platform
from dateutil.parser import parse as dtparse
import numpy as np
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from googleapiclient import discovery
import glob
import time
import json
import ipget
import slackweb
import locale


def gc_time_get():
    """Getting Google Calendar Event end time."""
    # If modifying these scopes, delete the file token.pickle.
    gc_scopes = ['https://www.googleapis.com/auth/calendar.readonly']
    # Shows basic usage of the Google Calendar API.
    # Prints the start and name of the next 10 events on the user's calendar.

    # Calendar id from Google_setting.json
    google_conf_file = os.path.join(pdirname, 'Google_setting.json')
    with open(google_conf_file, 'rb') as google_conf:
        google_conf_json = json.load(google_conf)
    g_calenderid = google_conf_json["calendarid"]

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials_gc.json', gc_scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC
    # print('Getting the upcoming 10 events')\
    calendarid = g_calenderid
    events_result = service.events().list(
        calendarId=calendarid, timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')

    i = 0
    event_no = None
    for event in events:
        for json_key in event['end']:
            if json_key == 'dateTime':
                event_no = i
                break
        if event_no is not None:
            break
        i += 1
    end_str = events[i]['end']['dateTime']
    end_obj = dtparse(end_str)
    tmfmt = '~%I:%M %p'
    return(datetime.datetime.strftime(end_obj, format=tmfmt))


def gdrive_upload(up_file_name):
    """Upload image to Google Drive for log."""
    """ Only for Linux"""
    gauth = GoogleAuth()
    gauth.CommandLineAuth()
    drive = GoogleDrive(gauth)

    google_conf_file = os.path.join(pdirname, 'Google_setting.json')
    with open(google_conf_file, 'rb') as google_conf:
        google_conf_json = json.load(google_conf)
    g_folder_id = google_conf_json["folder_id"]
    folder_id = g_folder_id

    f = drive.CreateFile({
        'title': os.path.basename(up_file_name),
        'mimeType': 'image/jpeg',
        'parents': [{'kind': 'drive#fileLink', 'id': folder_id}]})
    f.SetContentFile(up_file_name)
    f.Upload()


def write_log(slack_stat, slack_exp_uni):
    """Write log to Google Spreadsheet."""
    """Only for Linux"""
    time_now = datetime.datetime.now()
    log_time = time_now.strftime("[%Y/%m/%d %H:%M:%S]")
    unix_sec = str(time_now.timestamp())
    ip = ipget.ipget().ipaddr("wlan0")
    if slack_exp_uni == 0:
        slack_dur_sec = 0
        slack_dur_min = 0
    else:
        slack_exp = datetime.datetime.fromtimestamp(slack_exp_uni)
        slack_dur_sec = (slack_exp - time_now).total_seconds()
        slack_dur_min = slack_dur_sec / 60
        slack_dur_min = round(slack_dur_min / 10, 0) * 10

    creds = None
    gc_scopes = 'https://www.googleapis.com/auth/spreadsheets'
    if os.path.exists('token_gs.pickle'):
        with open('token_gs.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', gc_scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token_gs.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = discovery.build('sheets', 'v4', credentials=creds)

    # The ID of the spreadsheet to update.
    google_conf_file = os.path.join(pdirname, 'Google_setting.json')
    with open(google_conf_file, 'rb') as google_conf:
        google_conf_json = json.load(google_conf)
    spreadsheet_id = google_conf_json["spreadsheet_id"]

    # The A1 notation of a range to search for a logical table of data.
    # Values will be appended after the last row of the table.
    range_ = 'log_area'  # TODO: Update placeholder value.

    # How the input data should be interpreted.
    value_input_option = 'RAW'  # TODO: Update placeholder value.

    # How the input data should be inserted.
    insert_data_option = 'INSERT_ROWS'  # TODO: Update placeholder value.

    value_range_body = {
        # TODO: Add desired entries to the request body.
        "values": [[log_time, unix_sec, slack_stat, slack_dur_min, ip]]
    }
    request = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id, range=range_,
        valueInputOption=value_input_option,
        insertDataOption=insert_data_option, body=value_range_body)
    request.execute()


def overlay_icon(x, y, icon):
    """Image Overay."""
    global background
    hight, width, _ = icon.shape
    background[y:y + hight, x:x + width] = icon


def log_output(pdirname, ui_image, slack_stat, slack_exp_uni):
    """Save image as local log."""
    save_file_dir = os.path.join(pdirname, 'log')
    time_now = datetime.datetime.now()
    time_now_str = time_now.strftime("%m%d%H%M%S")
    save_file_name = time_now_str + "_" + slack_stat + ".jpg"
    save_file_name = os.path.join(save_file_dir, save_file_name)
    cv2.imwrite(save_file_name, ui_image)
    if platform.system() == "Linux":
        # Upload image to GoogleDrive
        gdrive_upload(save_file_name)
        # Save log
        write_log(slack_stat, slack_exp_uni)


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
        post_slack(mes_body)
        with open(ip_file_name, mode='w') as ip_file:
            ip_file.write(ip_addr)


def exp_check(slack_exp_uni):
    """Check exp soon."""
    now_unix = int(datetime.datetime.now().strftime('%s'))
    diff_unix = slack_exp_uni - now_unix
    if diff_unix // 60 <= 5:
        mes_body = "Within 5min, Slack Status will be expired."
        post_slack(mes_body)
    return(diff_unix // 60 <= 5)


def post_slack(mes_body):
    """Post message in Kazu channel."""
    slack = slackweb.Slack(url=slack_kazu_url)
    body = mes_body
    slack.notify(text=body)


def greet_word():
    """Decide greeting word based on time."""
    time_now = datetime.datetime.now()
    time_hour = int(time_now.strftime("%-H"))
    morning_hours = [6, 7, 8, 9]
    evening_hours = [17, 18, 19, 20, 21, 22, 23]

    if time_hour in morning_hours:
        return "Good morinig!", 0, 2.5
    elif time_hour in evening_hours:
        return "Good evening!", 0, 2.5
    else:
        return "Hello!", 80, 4

# Main Program
if __name__ == '__main__':
    err = 0
    cnt = 0
    slack_stat = ""
    slack_stat_old = ""
    slack_exp_uni_old = 0
    exp_ch_post = False
    if platform.system() == "Linux":
        os.chdir('/home/pi/Projects/SlackStatusUI')
    pdirname = os.getcwd()
    dirname = os.path.join(pdirname, "data")

    # Slack Seetings
    Slack_conf_file = os.path.join(pdirname, 'Slack_conf.json')
    with open(Slack_conf_file, 'rb') as Slack_conf:
        Slack_conf_json = json.load(Slack_conf)
    Slack_USER_TOKEN = Slack_conf_json['Slack_USER_TOKEN']
    Slack_USER_ID = Slack_conf_json['Slack_USER_ID']
    slack_kazu_url = Slack_conf_json['Slack_Kazu_channel']
    Slack_url_get = "https://slack.com/api/users.profile.get"
    Slack_url_set = "https://slack.com/api/users.profile.set"
    timeout_time = (3.0, 7.5)

    # Logo files load
    PAL_logo_file = os.path.join(dirname, 'FXPAL.png')

    while err == 0:
        data = {"token": Slack_USER_TOKEN, "user": Slack_USER_ID}
        img_file = ""
        try:
            slack_res_str = requests.get(
                Slack_url_get, params=data, timeout=timeout_time)
        except requests.exceptions.RequestException:
            post_slack("[Error!] Can't get slack status!1")
            time.sleep(30)
            try:
                slack_res_str = requests.get(
                    Slack_url_get, params=data, timeout=timeout_time)
            except requests.exceptions.RequestException:
                post_slack("[Error!] Can't get slack status!2")
                time.sleep(60)
                try:
                    slack_res_str = requests.get(
                        Slack_url_get, params=data, timeout=timeout_time)
                except requests.exceptions.RequestException:
                    post_slack("[Error!] Can't get slack status!3")
                    break
                else:
                    post_slack("Success to retry getting Slack status.")
            else:
                post_slack("Success to retry getting Slack status.")
        slack_json = slack_res_str.json()
        slack_stat = slack_json['profile']['status_text']
        slack_exp_uni = slack_json['profile']['status_expiration']
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        datestr = datetime.datetime.now().strftime("%a., %b. %d, %I:%M %p")

        print(cnt, datestr, ":[new]-", slack_stat, "[old]-", slack_stat_old)

        # slack_stat = 'Lunch'
        text_pos_x = 200
        text_pos_y = 290
        if slack_stat == 'Home':
            img_file = os.path.join(dirname, 'Home.png')
            text_str = 'At home'
            text_pos = (text_pos_x, text_pos_y)
            font_size = 4
        elif slack_stat == 'At work':
            img_file = os.path.join(dirname, 'Work.png')
            text_str = 'At office'
            text_pos = (text_pos_x, text_pos_y)
            font_size = 4
        elif slack_stat == 'At my office':
            img_file = os.path.join(dirname, 'Work.png')
            gw, offset, f_size = greet_word()
            text_str = gw
            text_pos = (text_pos_x + offset, text_pos_y)
            font_size = f_size
        elif slack_stat in ['Commuting', '通勤途中']:
            if slack_stat == '通勤途中':
                slack_stat = 'Commuting'
            img_file = os.path.join(dirname, 'Commuting.png')
            text_str = 'Commuting'
            text_pos = (text_pos_x, text_pos_y)
            font_size = 3
        elif slack_stat in ['In a meeting', '会議中']:
            if slack_stat == '会議中':
                slack_stat = 'In a meeting'
            img_file = os.path.join(dirname, 'Meeting.png')
            text_str = 'Meeting'
            text_pos = (text_pos_x, text_pos_y - 20)
            font_size = 4
        elif slack_stat == 'Lunch':
            img_file = os.path.join(dirname, 'lunch.png')
            text_str = 'Lunch'
            text_pos = (text_pos_x + 30, text_pos_y)
            font_size = 4
        elif slack_stat == 'Out of office':
            img_file = os.path.join(dirname, 'bluecar.png')
            text_str = 'Out of office'
            text_pos = (text_pos_x + 20, text_pos_y)
            font_size = 2.5
        elif slack_stat == 'At FXGI':
            img_file = os.path.join(dirname, 'Work.png')
            text_str = 'At FXGI'
            text_pos = (text_pos_x, text_pos_y)
            font_size = 4
        elif slack_stat in ['Working remotely', 'リモートで作業中']:
            if slack_stat == 'リモートで作業中':
                slack_stat == 'Working remotely'
            img_file = os.path.join(dirname, 'computer.png')
            text_str = 'Working remotely'
            text_pos = (text_pos_x, text_pos_y)
            font_size = 2
        elif slack_stat in ['Absence', '病欠']:
            if slack_stat == '病欠':
                slack_stat = 'Absence'
            img_file = os.path.join(dirname, 'absence.png')
            text_str = 'Absence'
            text_pos = (text_pos_x, text_pos_y)
            font_size = 4
        elif slack_stat == 'Trip':
            img_file = os.path.join(dirname, 'trip.png')
            text_str = 'Trip'
            text_pos = (text_pos_x + 80, text_pos_y)
            font_size = 4
        elif slack_stat == "":
            slack_stat = 'At work'
            img_file = os.path.join(dirname, 'Work.png')
            text_str = 'At office'
            text_pos = (text_pos_x, text_pos_y)
            font_size = 4
            profile = {
                "status_text": slack_stat,
                "status_emoji": ":office:",
                "status_expiration": 0}
            profile = json.dumps(profile)
            data["profile"] = profile
            slack_res_str_post = requests.post(
                Slack_url_set, data=data, timeout=timeout_time)

        if os.path.exists(img_file) is False:
            print(slack_stat)
            print(img_file)
            print('error no ICON file')
            mes_body = "Doesn't much status. slack_stat: " + slack_stat
            post_slack(mes_body)

        # Overlay Logo
        background = np.zeros(shape=(480, 810, 3), dtype=np.uint8)
        background[:120, :, :] = 70
        background[410:, :, :] = 70
        icon = cv2.imread(PAL_logo_file)
        overlay_icon(30, 10, icon)

        # Write Title on image
        ui_image = cv2.putText(
            background, "Kazu's status", (150, 70),
            cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
            2.5, (200, 200, 200), 3, cv2.LINE_AA)

        # Write Titile on image
        ui_image = cv2.putText(
            ui_image, "from Slack", (570, 110),
            cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
            1, (150, 150, 150), 2, cv2.LINE_AA)

        # Overlay ICON
        icon = cv2.imread(img_file)
        overlay_icon(30, 140, icon)

        # Write Current time on image
        ui_image = cv2.putText(
            ui_image, datestr, (450, 450),
            cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
            0.8, (150, 150, 150), 1, cv2.LINE_AA)

        # Write Status on image
        ui_image = cv2.putText(
            ui_image, text_str, text_pos,
            cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
            font_size, (200, 200, 200), 5, cv2.LINE_AA)

        # Write end time
        if text_str in [
                'Meeting', 'Out of office',
                'At FXGI', 'Absence',
                'Working remotely', 'Trip']:
            print(slack_exp_uni)
            if slack_exp_uni != 0:
                slack_exp = datetime.datetime.fromtimestamp(slack_exp_uni)
                slack_end = slack_exp.strftime("~%I:%M %p")
                ui_image = cv2.putText(
                    ui_image, slack_end, (400, 370),
                    cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
                    2, (200, 200, 200), 3, cv2.LINE_AA)

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

            if platform.system() == "Linux":
                ip_check()

        # Check expire soon
        if slack_exp_uni != slack_exp_uni_old:
            exp_ch_post = False
        if exp_ch_post is False and slack_exp_uni != 0:
            exp_ch_post = exp_check(slack_exp_uni)

        # Write image and log for history when change status
        if slack_stat != slack_stat_old:
            exp_ch_post = False
            log_output(pdirname, ui_image, slack_stat, slack_exp_uni)
            mes_body = "Changed to [" + slack_stat + "] from ["\
                + slack_stat_old + "]"
            post_slack(mes_body)

        # Wait 20sec
        time.sleep(20)
        slack_stat_old = slack_stat
        slack_exp_uni_old = slack_exp_uni

        cnt += 1
        time_now = datetime.datetime.now()
        hourstr = time_now.strftime("%H")
        minstr = time_now.strftime("%M")
        if int(hourstr) >= 22 and int(minstr) >= 50:
            log_output(pdirname, ui_image, slack_stat, slack_exp_uni)
            break

cv2.waitKey(10)
cv2.destroyAllWindows()
for i in range(1, 5):
    cv2.waitKey(1)
