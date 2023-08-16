from slackclient import SlackClient
import requests
import json
import os
import re

def get_client(slack_token):

    return SlackClient(slack_token)

def get_prod_incidents_list():

    client = get_client(os.environ['SLACK_TOKEN'])

    response = client.api_call(
        "conversations.info",
        channel=os.environ['PRODUCTION_CHANNEL']
    )['channel']['topic']['value']

    match_string = re.search("Open incidents: (.*)(?:\s[|])", response)

    if match_string:
        return "There are open incidents in the production Slack channel: {}".format(match_string[1])
    else:
        return "There are no open incidents on the production Slack channel"

def post_to_slack(channel_to_post, payload_message, text_message, thread_to_post = None):

    client = get_client(os.environ['SLACK_MEESEEKS_API_KEY'])

    # The message to be posted to slack is a more complex model using Slack blocks
    # needs to use this structure https://api.slack.com/tools/block-kit-builder
    # the text field is just an requirement
    kwargs = {
        "channel":channel_to_post,
        "text":text_message,
        "blocks":payload_message
    }

    if thread_to_post:
        kwargs["thread_ts"] = thread_to_post

    response = client.api_call(
        'chat.postMessage',
        **kwargs
    )

    if not response['ok']:
        return "A problem happened to post to Slack"
    return response
