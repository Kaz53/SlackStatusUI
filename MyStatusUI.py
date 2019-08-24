"""Showing status from Slack."""
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


def write_log(time_now, slack_stat):
    """Write log to Google Spreadsheet."""
    log_time = time_now.strftime("[%Y/%m/%d %H:%M:%S]")
    unix_sec = str(time_now.timestamp())
    # log_out = log_time + ',' + slack_stat

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
        spreadsheet_id = '1XuVWBl_R4twkBdgfmL6VUadcbNJX9lCsbTERUbUJMCM'

        # The A1 notation of a range to search for a logical table of data.
        # Values will be appended after the last row of the table.
        range_ = 'log_area'  # TODO: Update placeholder value.

        # How the input data should be interpreted.
        value_input_option = 'RAW'  # TODO: Update placeholder value.

        # How the input data should be inserted.
        insert_data_option = 'INSERT_ROWS'  # TODO: Update placeholder value.

        value_range_body = {
            # TODO: Add desired entries to the request body.
            "values": [[log_time, unix_sec, slack_stat]]
        }
        request = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range_,
            valueInputOption=value_input_option,
            insertDataOption=insert_data_option, body=value_range_body)
        request.execute()


def overlay_icon(x, y):
    """Image Overay."""
    global background
    hight, width, _ = icon.shape
    background[y:y + hight, x:x + width] = icon


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

    while err == 0:
        data = {"token": Slack_USER_TOKEN, "user": Slack_USER_ID}
        img_file = ""
        background = np.zeros(shape=(450, 795, 3), dtype=np.uint8)
        slack_res_str = requests.get(Slack_url_get, params=data)
        slack_json = slack_res_str.json()
        slack_stat = slack_json['profile']['status_text']
        slack_exp_uni = slack_json['profile']['status_expiration']
        datestr = datetime.datetime.now().strftime("%a., %b. %d, %I:%M %p")
        """dummy_stat = 'In a meeting'
        slack_stat = dummy_stat"""

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
            text_pos = (300, 270)
            font_size = 3
        else:
            slack_stat == 'At work'
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
            slack_res_str = requests.post(Slack_url_set, data=data)

        if os.path.exists(img_file) is False:
            print(slack_stat)
            print(img_file)
            print('error no ICON file')

        icon = cv2.imread(img_file)
        overlay_icon(30, 120)
        # Write Title on image
        ui_image = cv2.putText(
            background, "Kazu's status", (20, 70),
            cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
            2, (200, 200, 200), 3, cv2.LINE_AA)
        # Write Titile on image
        ui_image = cv2.putText(
            ui_image, "from Slack", (490, 70),
            cv2.FONT_HERSHEY_DUPLEX | cv2.FONT_ITALIC,
            1, (200, 200, 200), 2, cv2.LINE_AA)
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
        if text_str == 'Meeting':
            slack_exp = datetime.datetime.fromtimestamp(slack_exp_uni)
            slack_exp = slack_exp.strftime("~%I:%M %p")
            meeting_end = slack_exp
            ui_image = cv2.putText(
                ui_image, meeting_end, (400, 350),
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
        if slack_stat != slack_stat_old:
            save_file_dir = os.path.join(pdirname, 'log')
            time_now = datetime.datetime.now()
            time_now_str = time_now.strftime("%m%d%H%M%S")
            save_file_name = time_now_str + "_" + slack_stat + ".jpg"
            save_file_name = os.path.join(save_file_dir, save_file_name)
            cv2.imwrite(save_file_name, ui_image)
            gdrive_upload(save_file_name)
            write_log(time_now, slack_stat)

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
