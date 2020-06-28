# /tag --repo=inirepo --commit=hashcom --tag=initagnya

import os
import requests

# slack
from slack import WebClient
from slack.errors import SlackApiError

# sanic
from sanic import Sanic
from sanic.response import json

TOKEN = os.environ['SLACK_API_TOKEN']
UTL_GET_PROFILE = 'https://slack.com/api/users.profile.get'
TO_CHANNEL = '#channel_gimbot'
LIST_COMMAND = ['repo', 'commit', 'tag']

# open client slack
client = WebClient(
    token=TOKEN,
    run_async=True # turn async mode on
)
# Define this as an async function to post message 
async def send_to_slack(channel, text):
    try:
        # Don't forget to have await as the client returns asyncio.Future
        response = await client.chat_postMessage(
            channel=channel,
            text=text
        )

    except SlackApiError as e:
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        raise e

app = Sanic('BOT')
@app.route('/tag', methods=['POST'])
async def tag_git(request):

    # get profile
    profile = requests.get('{0}?token={1}&user={2}&pretty=1'.format(UTL_GET_PROFILE, TOKEN, request.form.get('user_id')))

    if profile.status_code == 200:
        user_profile = profile.json().get('profile')

        try:
            # get text command
            text = request.form.get('text')
            text_split = text.split(' ')
            for ts in text_split:
                # checking start with --
                ts_des = (ts.split('--', 1)[1]).split('=')
                ts_command = ts_des[0]
                ts_val = ts_des[1]

                if ts_command in LIST_COMMAND:
                    # GIT PROCESS
                    pass

                else:
                    return json({'message': 'Invalid syntax'})

            await send_to_slack(channel=TO_CHANNEL, text='Hallo {}'.format(user_profile.get('email')))

            return json({'message': 'Done!'})

        except SlackApiError as e:

            return json({'message': f"Failed due to {e.response['error']}"})

        except Exception as e:
            return json({'message': 'Invalid syntax'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2424)