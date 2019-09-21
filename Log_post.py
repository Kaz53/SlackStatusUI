"""Post error message to Slack."""
import slackweb
import json
import os
import platform


def post_slack(mes_body):
    """Post message in Kazu channel."""
    slack = slackweb.Slack(url=slack_kazu_url)
    body = mes_body
    slack.notify(text=body)

if __name__ == '__main__':
    if platform.system() == "Linux":
        os.chdir('/home/pi/Projects/SlackStatusUI')
    pdirname = os.getcwd()
    dirname = os.path.join(pdirname, "data")

    # Slack Seetings
    Slack_conf_file = os.path.join(pdirname, 'Slack_conf.json')
    with open(Slack_conf_file, 'rb') as Slack_conf:
        Slack_conf_json = json.load(Slack_conf)
    slack_kazu_url = Slack_conf_json['Slack_Kazu_channel']

    # Read error log
    error_log_file = open(os.path.join(pdirname, 'log.txt'))
    if os.path.exists(error_log_file):
        error_log = error_log_file.read()
        error_log_file.close()

        if error_log != "":
            post_slack(error_log)
