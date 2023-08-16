import os
import boto3

ssm_client = boto3.client(
    'ssm',
    region_name=os.environ["AWS_DEFAULT_REGION"]
)

os.environ['DEBUG'] = ssm_client.get_parameter(Name='/debug')['Parameter']['Value']

os.environ['GITHUB_TOKEN'] = ssm_client.get_parameter(Name='/github-token', WithDecryption=True)['Parameter']['Value']
os.environ['PAGERDUTY_TOKEN'] = ssm_client.get_parameter(Name='/pagerduty-token', WithDecryption=True)['Parameter']['Value']
os.environ['OCTOPUS_API_KEY'] = ssm_client.get_parameter(Name='/octopus-api-key', WithDecryption=True)['Parameter']['Value']
os.environ['SLACK_TOKEN'] = ssm_client.get_parameter(Name='/slack-token', WithDecryption=True)['Parameter']['Value']
os.environ['SLACK_MEESEEKS_API_KEY'] = ssm_client.get_parameter(Name='/slack-meeseeks-api-key', WithDecryption=True)['Parameter']['Value']
os.environ['WOLFRAM_ALPHA_API_ID'] = ssm_client.get_parameter(Name='/wolfram-alpha-api-id', WithDecryption=True)['Parameter']['Value']

os.environ['PRODUCTION_CHANNEL'] = ssm_client.get_parameter(Name='/production-channel')['Parameter']['Value']
os.environ['SLACK_CHANNEL'] = ssm_client.get_parameter(Name='/slack-channel')['Parameter']['Value']
os.environ['SLACK_SERVICE_ID'] = ssm_client.get_parameter(Name='/pd-service-id')['Parameter']['Value']

os.environ['BOT_PREFIXES'] = ssm_client.get_parameter(Name='/bot-prefixes')['Parameter']['Value']

os.environ['ACL_ALLOWED_CHANNELS'] = ssm_client.get_parameter(Name='/acl-allowed-channels')['Parameter']['Value']
os.environ['ACL_ALLOWED_USERS'] = ssm_client.get_parameter(Name='/acl-allowed-users')['Parameter']['Value']

os.environ['NR_BASE_URL'] = ssm_client.get_parameter(Name='/newrelic_base_url')['Parameter']['Value']
os.environ['NR_USER_ID'] = ssm_client.get_parameter(Name='/newrelic_user_id')['Parameter']['Value']
os.environ['NR_PS_ACCOUNT_ID'] = ssm_client.get_parameter(Name='/newrelic_ps_account_id')['Parameter']['Value']
os.environ['NR_PS_API_KEY'] = ssm_client.get_parameter(Name='/newrelic_ps_api_key', WithDecryption=True)['Parameter']['Value']
os.environ['NR_PRAC_ACCOUNT_ID'] = ssm_client.get_parameter(Name='/newrelic_prac_account_id')['Parameter']['Value']
os.environ['NR_PRAC_API_KEY'] = ssm_client.get_parameter(Name='/newrelic_prac_api_key', WithDecryption=True)['Parameter']['Value']

os.environ['MW_SLACK_CHANNEL'] = ssm_client.get_parameter(Name='/mw-notification/slack-channel')['Parameter']['Value']
os.environ['MW_TEMPLATE_URL'] = ssm_client.get_parameter(Name='/mw-notification/template-url')['Parameter']['Value']
