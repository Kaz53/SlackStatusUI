import json
import os
import pickle
import ipget
import time
import datetime
import platform
import cv2
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from googleapiclient import discovery

import util_slack


def gdrive_upload(pdirname, up_file_name):
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


def write_log(pdirname, slack_stat, slack_exp_uni):
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
    try:
        request.execute()
    except socket.timeout:
            time.sleep(30)
            request.execute()
            util_slack.post_slack("Success to retry writing log in spreadsheet.")


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
        gdrive_upload(pdirname, save_file_name)
        # Save log
        write_log(pdirname, slack_stat, slack_exp_uni)


def write_temp_log(pdirname, params):

    """Write parameters to Google Spreadsheets."""
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
    range_ = 'temp_log'  # TODO: Update placeholder value.

    # How the input data should be interpreted.
    value_input_option = 'RAW'  # TODO: Update placeholder value.

    # How the input data should be inserted.
    #insert_data_option = 'INSERT_ROWS'  # TODO: Update placeholder value.

    value_range_body = {
        # TODO: Add desired entries to the request body.
        "values": [params]
    }
    request = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id, range=range_,
        valueInputOption=value_input_option,
        #insertDataOption=insert_data_option,
         body=value_range_body)
    #try:
    request.execute()
    #except socket.timeout:
            #time.sleep(30)
            #request.execute()
            #util_slack.post_slack("Success to retry writing log in spreadsheet.")
