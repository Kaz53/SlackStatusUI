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
    # for event in events:
        # start = event['start'].get('dateTime', event['start'].get('date'))
        # print(start,event['summary'])

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


def write_log(time_now, slack_stat, slack_exp_uni):
    """Write log to Google Spreadsheet."""
    log_time = time_now.strftime("[%Y/%m/%d %H:%M:%S]")
    unix_sec = str(time_now.timestamp())
    if slack_exp_uni == 0:
        slack_dur_sec = 0
        slack_dur_min = 0
    else:
        slack_exp = datetime.datetime.fromtimestamp(slack_exp_uni)
        slack_dur_sec = (slack_exp - time_now).total_seconds()
        slack_dur_min = slack_dur_sec / 60
        slack_dur_min = round(slack_dur_min, 0)

    if platform.system() == "Linux":
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
            "values": [[log_time, unix_sec, slack_stat, slack_dur_min]]
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


def overlay_icon2(x, y, icon):
    """Image Overay2."""
    global background
    hight, width, _ = icon.shape
    mask = icon[:, :, 3]
    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    # mask = mask / 255.0
    icon = icon[:, :, :3]

    background[y:y + hight, x:x + width] *= 1 - mask
    background[y:y + hight, x:x + width] += icon + mask


# Main Program
if __name__ == '__main__':
    err = 0
    cnt = 0
    slack_stat = ""
    slack_stat_old = ""
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
    Slack_url_get = "https://slack.com/api/users.profile.get"
    Slack_url_set = "https://slack.com/api/users.profile.set"

    # Logo files load
    PAL_logo_file = os.path.join(dirname, 'FXPAL.png')
    FX_logo_file = os.path.join(dirname, "FX.png")

    while err == 0:
        data = {"token": Slack_USER_TOKEN, "user": Slack_USER_ID}
        img_file = ""
        slack_res_str = requests.get(Slack_url_get, params=data)
        slack_json = slack_res_str.json()
        slack_stat = slack_json['profile']['status_text']
        slack_exp_uni = slack_json['profile']['status_expiration']
        datestr = datetime.datetime.now().strftime("%a., %b. %d, %I:%M %p")

        # slack_stat = 'At FXGI'
        if slack_stat == 'Home':
            img_file = os.path.join(dirname, 'Home.png')
            text_str = 'At home'
            text_pos = (200, 270)
            font_size = 4
        elif slack_stat == 'At work':
            img_file = os.path.join(dirname, 'Work.png')
            text_str = 'At office'
            text_pos = (200, 270)
            font_size = 4
        elif slack_stat == 'Commuting':
            img_file = os.path.join(dirname, 'Commuting.png')
            text_str = 'Commuting'
            text_pos = (200, 270)
            font_size = 3
        elif slack_stat == 'In a meeting':
            img_file = os.path.join(dirname, 'Meeting.png')
            text_str = 'Meeting'
            text_pos = (200, 250)
            font_size = 4
        elif slack_stat == 'Lunch':
            img_file = os.path.join(dirname, 'lunch.png')
            text_str = 'Lunch'
            text_pos = (200, 270)
            font_size = 4
        elif slack_stat == 'Out of office':
            img_file = os.path.join(dirname, 'bluecar.png')
            text_str = 'Out of office'
            text_pos = (220, 270)
            font_size = 2.5
        elif slack_stat == 'At FXGI':
            img_file = os.path.join(dirname, 'Work.png')
            text_str = 'At FXGI'
            text_pos = (200, 270)
            font_size = 4
        elif slack_stat == "":
            slack_stat = 'At work'
            img_file = os.path.join(dirname, 'Work.png')
            text_str = 'At office'
            text_pos = (200, 270)
            font_size = 4
            profile = {
                "status_text": slack_stat,
                "status_emoji": ":office:",
                "status_expiration": 0}
            profile = json.dumps(profile)
            data["profile"] = profile
            slack_res_str_post = requests.post(Slack_url_set, data=data)

        if os.path.exists(img_file) is False:
            print(slack_stat)
            print(img_file)
            print('error no ICON file')

        # Overlay Logo
        background = np.zeros(shape=(450, 795, 3), dtype=np.uint8)
        # icon = cv2.imread(FX_logo_file, cv2.IMREAD_UNCHANGED)
        # overlay_icon2(10, 330, icon)
        background = background[:, :, :3]
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
            1, (200, 200, 200), 2, cv2.LINE_AA)

        # Overlay ICON
        icon = cv2.imread(img_file)
        overlay_icon(30, 120, icon)

        # Write Current time on image
        ui_image = cv2.putText(
            ui_image, datestr, (450, 420),
            cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
            0.8, (200, 200, 200), 1, cv2.LINE_AA)
        # Write Status on image
        ui_image = cv2.putText(
            ui_image, text_str, text_pos,
            cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
            font_size, (200, 200, 200), 5, cv2.LINE_AA)

        # Write Meeting end time
        if text_str == 'Meeting' or text_str == 'Out of office' or text_str == 'At FXGI':
            slack_exp = datetime.datetime.fromtimestamp(slack_exp_uni)
            slack_end = slack_exp.strftime("~%I:%M %p")
            ui_image = cv2.putText(
                ui_image, slack_end, (400, 350),
                cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
                2, (200, 200, 200), 3, cv2.LINE_AA)

        cv2.imshow("MyStatus", ui_image)
        cv2.waitKey(1)

        # Initial image position adjustment
        if cnt == 0:
            cv2.waitKey(1000)
            cv2.moveWindow("MyStatus", 0, -5)
            cv2.imshow("MyStatus", ui_image)
            cv2.waitKey(1)

            file_list = glob.glob("./log/*jpg")
            for file in file_list:
                os.remove(file)

        # Write image and log for history when change status
        if slack_stat != slack_stat_old or slack_stat == "":
            save_file_dir = os.path.join(pdirname, 'log')
            time_now = datetime.datetime.now()
            time_now_str = time_now.strftime("%m%d%H%M%S")
            save_file_name = time_now_str + "_" + slack_stat + ".jpg"
            save_file_name = os.path.join(save_file_dir, save_file_name)
            cv2.imwrite(save_file_name, ui_image)
            gdrive_upload(save_file_name)
            write_log(time_now, slack_stat, slack_exp_uni)

        # Wait 20sec
        time.sleep(20)
        slack_stat_old = slack_stat

        cnt += 1
        if cnt == 10000:
            break

cv2.waitKey(10)
cv2.destroyAllWindows()
for i in range(1, 5):
    cv2.waitKey(1)
