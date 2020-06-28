# /tag --repo=inirepo --commit=hashcom --tag=initagnya

import os

import requests
from requests.auth import HTTPBasicAuth
# sanic
from sanic import Sanic
from sanic.response import json, json_dumps
# slack
from slack import WebClient
from slack.errors import SlackApiError

TOKEN = os.environ['SLACK_API_TOKEN']
UTL_GET_PROFILE = 'https://slack.com/api/users.profile.get'
TO_CHANNEL = '#channel_gimbot'
LIST_COMMAND = ['repo', 'commit', 'tag']
URL_GIT = 'https://api.github.com'
USER_GIT = os.environ['USER_GIT']
PSWD_GIT = os.environ['PSWD_GIT']

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

            __repo = None
            __commit_hash = None
            __tag_name = None

            for ts in text_split:
                # checking start with --
                ts_des = (ts.split('--', 1)[1]).split('=')
                ts_command = ts_des[0]
                ts_val = ts_des[1]
                
                if ts_command not in LIST_COMMAND:
                    return json({'message': 'Invalid syntax'})

                if ts_command == 'repo':
                    __repo = ts_val
                    
                elif ts_command == 'commit':
                    __commit_hash = ts_val
                
                elif ts_command == 'tag':
                    __tag_name = ts_val

            # GIT PROCESS

            # git_process = requests.get('https://api.github.com/user', auth=HTTPBasicAuth(USER_GIT, 'PSWD_GIT'))
            # print(git_process)

            # POST /repos/:owner/:repo/git/refs
            # url_ref = "{}/repos/{}/{}/git/refs".format(URL_GIT, 'sendaljpt', 'slack-bot')
            # data_ref = {
            #     "ref": "refs/heads/master",
            #     "sha": "78bb29d32bd3142307649b40ed0774934be3cc9c"
            # }

            # post_ref = requests.post(url_ref, data = json_dumps(data_ref), auth = (USER_GIT, PSWD_GIT))

            # print(post_ref)

            # create TAGS
            # POST /repos/:owner/:repo/git/tags
            # url_tag = '{}/repos/{}/{}/git/tags'.format(URL_GIT, 'sendaljpt', 'slack-bot')
            # data_tags = {
            #     "tag": "development",
            #     "message": "tag release devel",
            #     "object": "78bb29d32bd3142307649b40ed0774934be3cc9c",
            #     "type": "commit",
            #     "tagger": {
            #         "name": "Fajrin Imam Arif",
            #         "email": "sendaljpt24@gmail.com",
            #         "date": "2020-06-29T14:53:35-07:00"
            #     }
            # }
            # post_tags = requests.post(url_tag, data = json_dumps(data_tags), auth = (USER_GIT, PSWD_GIT))

            # MAKE RELEASE TAGS
            # POST /repos/:owner/:repo/releases

            url_release = '{}/repos/{}/{}/releases'.format(URL_GIT, USER_GIT, __repo)
            data_release = {
                "tag_name": __tag_name,
                "target_commitish": __commit_hash,
                "name": __tag_name,
                "body": "Release to {}".format(__tag_name),
                "draft": False,
                "prerelease": False,
            }

            post_release = requests.post(url_release, data = json_dumps(data_release), auth = (USER_GIT, PSWD_GIT))

            await send_to_slack(channel=TO_CHANNEL, text='Hallo {}'.format(user_profile.get('email')))

            return json({'message': 'Done!'})

        except SlackApiError as e:

            return json({'message': f"Failed due to {e.response['error']}"})

        except Exception as e:
            return json({'message': 'Invalid syntax'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2424)