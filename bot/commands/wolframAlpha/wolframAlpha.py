from errbot import BotPlugin, botcmd
import wolframalpha
import os

class WolframAlpha(BotPlugin):

    # Define the wa as the call for the wolfram alpha command query
    @botcmd
    def wa(self, msg, arg):
        """This function searchs any information on the WolframAlpha engine
        It only shows the result on the plaintext field of the json response
        of the api query"""

        if arg:
            yield "Ooohhh can do, let me search that.. "

            client = wolframalpha.Client(os.environ["WOLFRAM_ALPHA_API_ID"])

            answer  = ""
            ask = client.query(arg)

            try:
                for pod in ask.pods:
                    if pod.title in ["Result", "Results"]:
                        for sub in pod.subpods:
                            answer += sub.plaintext
            except AttributeError:
                log.info("KeyError triggered on retrieving pods.")

            if answer:
                yield "This is your answer: {}".format(answer)
            else:
                yield "You probably didn't ask me right, I've found nothing.."

        else:
            yield "Ooohhh, you need to say something for me to search on Wolfram Alpha.."
