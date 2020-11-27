"""Post error message to Slack."""
import slackweb
import json
import os
import platform

# Slack Seetings
Slack_conf_file = os.path.join(pdirname, 'Slack_conf.json')
with open(Slack_conf_file, 'rb') as Slack_conf:
    Slack_conf_json = json.load(Slack_conf)
# slack_kazu_url = Slack_conf_json['Slack_Kazu_channel']
slack_post = "https://slack.com/api/chat.postMessage"
Slack_USER_TOKEN_FFR = Slack_conf_json['Slack_USER_TOKEN_FFR']
Slack_USER_ID_FFR = Slack_conf_json['Slack_USER_ID_FFR']
data_ffr = {"token": Slack_USER_TOKEN_FFR, "user": Slack_USER_ID_FFR}


def post_slack(mes_body):
    # """Post message in Kazu channel."""
    # slack = slackweb.Slack(url=slack_kazu_url)
    # body = mes_body
    # slack.notify(text=body)
    """Post message to me."""
    post_data = {
                "channel": Slack_USER_ID_FFR,
                "text": mes_body
                }
    headers = {"Authorization": "Bearer "+Slack_USER_TOKEN_FFR}
    requests.post(slack_post, headers=headers, data=post_data, timeout=timeout_time)

if __name__ == '__main__':
    if platform.system() == "Linux":
        os.chdir('/home/pi/Projects/SlackStatusUI')
    pdirname = os.getcwd()


    # Read error log
    error_log_file = open(os.path.join(pdirname, 'log/log.txt'))
    error_log = error_log_file.read()
    error_log_file.close()

    if error_log != "":
        post_slack(error_log)
