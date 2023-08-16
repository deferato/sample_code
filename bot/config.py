import logging
import os
import config_env

BACKEND = 'Slack'

# Bot data cache repository
BOT_DATA_DIR = '/bot/data'

# Functions/commands repository
BOT_EXTRA_PLUGIN_DIR = '/bot/commands'

BOT_LOG_FILE = '/bot/logs/errbot_DEBUG.log'
BOT_LOG_LEVEL = logging.os.environ['DEBUG']

BOT_IDENTITY = {
    "token": os.environ['SLACK_TOKEN']
}

# Not in use, but necessary configs
CHATROOM_PRESENCE = ()
BOT_PLUGIN_INDEXES = '/bot/repos.json'
BOT_ADMINS = ()

# Prefixes for the bot name calling
BOT_ALT_PREFIX_CASEINSENSITIVE = True

BOT_ALT_PREFIXES = os.environ['BOT_PREFIXES'].split(',')

array_allowed_channels =  os.environ['ACL_ALLOWED_CHANNELS'].replace(' ', '').split(',')
array_allowed_users =  os.environ['ACL_ALLOWED_USERS'].replace(' ', '').split(',')

ACCESS_CONTROLS = {'*': {'allowrooms': array_allowed_channels },
                   '*': {'allowusers': array_allowed_users } }
