from errbot import BotPlugin, re_botcmd
from commands._helpers import octopus, slack
import json

class StepTemplate(BotPlugin):

    @re_botcmd(pattern=r"(?:step|steptemplate|stepstatus)")
    def get_step_update_status(self, msg, match):
        """This commands searches on the Octopus API for Projects
        using and older version of the Step Templates
        and generate a message to the slack with the list"""

        self._bot.add_reaction(msg, "hourglass")

        OCTOPUS_URL = "https://octopus.com/app#/Spaces-1/"
        template_list = octopus.get_step_template_list()

        # Receives the channel id where the message was posted
        channel_to_post = msg.frm.channelid
        template_old_usage = []

        if 'ErrorMessage' in template_list:
            self._bot.remove_reaction(msg, "hourglass")
            self._bot.add_reaction(msg, "warning")
            yield "Octopus Error: {}".format(template_list['ErrorMessage'])
            return

        # Iterate through Octopus API to get the list of Step Templates
        for template in template_list:
            if not template['CommunityActionTemplateId']:

                template_usage = octopus.get_template_usage(template['Links']['Usage'])

                if template_usage:
                    template_usage_list = []

                    for usage in template_usage:
                        if int(usage['Version']) < int(template['Version']):
                            template_usage_list.append({
                                'Name' : usage['ProjectName'],
                                'Version' : usage['Version']
                            })

                    if template_usage_list:
                        template_url = OCTOPUS_URL + "library/steptemplates/" + template['Id'] + "/usage"
                        template_old_usage.append({
                            'Name' : template['Name'],
                            'Version' : template['Version'],
                            'TemplateUrl' : template_url,
                            'Usage' : template_usage_list,
                        })

        # if there's projects using an old step template version, start building a json message to post to slack
        if template_old_usage:
            payload_message = [
                {
                    "type" : "section",
                    "text" : {
                        "type" : "mrkdwn",
                        "text" : "The following *Projects* are using an older version of the *Step Templates*:"
                    }
                },
                {
                    "type" : "divider"
                },
                {
                    "type" : "section",
                    "fields" : [
                        {
                            "type" : "mrkdwn",
                            "text" : "*Step Template:*"
                        },
                        {
                            "type" : "mrkdwn",
                            "text" : "*Version:*"
                        }
                    ]
                }
            ]

            for template in template_old_usage:
                step_name = ''
                step_version = ''
                count_limit = 0

                for usage in template['Usage']:
                    step_name += ">{}\n".format(usage['Name'])
                    step_version += "{}\n".format(usage['Version'])

                    count_limit += 1
                    if count_limit >= 5:
                        step_name += "<{}|More..>\n".format(template['TemplateUrl'])
                        step_version += "\n"
                        break

                payload_message.append(
                    {
                        'type' : 'section',
                        'fields' : [
                            {
                                'type' : 'mrkdwn',
                                'text' : "<{}|{}>".format(template['TemplateUrl'], template['Name'])
                            },
                            {
                                'type' : 'mrkdwn',
                                'text' : "{}".format(template['Version'])
                            },
                            {
                                'type' : 'mrkdwn',
                                'text' : step_name
                            },
                            {
                                'type' : 'mrkdwn',
                                'text' : step_version
                            }
                        ]
                    }
                )

            slack.post_to_slack(channel_to_post, payload_message, 'Notify Octopus Step Template changes')
            self._bot.remove_reaction(msg, "hourglass")
            self._bot.add_reaction(msg, "heavy_check_mark")
