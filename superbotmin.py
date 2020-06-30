# /tag --repo=slack-bot --commit=78bb29d32bd3142307649b40ed0774934be3cc9c --tag=staging
# /tag --repo=slack-bot --commit=f62fd5c52871ba375eb4751b9f2947abe553ebcd --tag=development

import os
import json as JSon

import requests
from requests.auth import HTTPBasicAuth
# sanic
from sanic import Sanic
from sanic.response import json, json_dumps
# slack
from slack import WebClient
from slack.errors import SlackApiError

# SET GLOBAL VARIABLE
TOKEN = os.environ['SLACK_API_TOKEN']
URL_GET_PROFILE = 'https://slack.com/api/users.profile.get'
TO_CHANNEL = '#history_superbotmin'
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
    profile = requests.get('{0}?token={1}&user={2}&pretty=1'.format(URL_GET_PROFILE, TOKEN, request.form.get('user_id')))

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

            # MAKE RELEASE TAGS
            if __repo != None and __commit_hash != None and __tag_name != None:

                # check tag if exist
                # GET /repos/:owner/:repo/releases/tags/:tag
                url_check_tag = '{}/repos/{}/{}/releases/tags/{}'.format(URL_GIT, USER_GIT, __repo, __tag_name)
                check_tag = requests.get(url_check_tag, auth=HTTPBasicAuth(USER_GIT, PSWD_GIT))
                # if exist update tag
                if check_tag.status_code == 200:
                    existing_tag_release = check_tag.json()
                    # do update
                    # PATCH /repos/:owner/:repo/releases/:release_id
                    url_update_tag = '{}/repos/{}/{}/releases/{}'.format(URL_GIT, USER_GIT, __repo, existing_tag_release.get('id'))

                    data_release = {
                        "tag_name": __tag_name,
                        "target_commitish": __commit_hash,
                        "name": __tag_name,
                        "body": "Update Release to {}".format(__tag_name),
                        "draft": False,
                        "prerelease": False,
                    }

                    patch_release = requests.patch(url_update_tag, data = json_dumps(data_release), auth = (USER_GIT, PSWD_GIT))

                    # after update tag release we must update refs commit of tag
                    # POST /repos/:owner/:repo/git/refs
                    url_ref = "{}/repos/{}/{}/git/refs/tags/{}".format(URL_GIT, 'sendaljpt', 'slack-bot', __tag_name)
                    data_ref = {
                        "sha": __commit_hash,
                        "force": True
                    }
                    patch_ref = requests.patch(url_ref, data = json_dumps(data_ref), auth = (USER_GIT, PSWD_GIT))

                
                # if not exist create new tag
                # POST /repos/:owner/:repo/releases
                elif check_tag.status_code == 404:
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

                message_slack = "{} tags {} with a commit {}".format(user_profile.get('email'), __tag_name, __commit_hash)
                await send_to_slack(channel=TO_CHANNEL, text=message_slack)

                return json({'message': 'Done!'})

            return json({'message': 'Invalid syntax'})

        except SlackApiError as e:

            return json({'message': f"Failed due to {e.response['error']}"})

        except Exception as e:
            return json({'message': 'Invalid syntax'})


@app.route('/tag-menu', methods=['POST'])
async def tag_menu(request):

    request_data = request.form.get('payload')
    if request_data != None:
        data_req = JSon.loads(request_data)
        __repo = data_req['submission']['repo']
        __commit_hash = data_req['submission']['commit_hash']
        __tag_name = data_req['submission']['tag_name']

        # get profile
        profile = requests.get('{0}?token={1}&user={2}&pretty=1'.format(URL_GET_PROFILE, TOKEN, data_req['user']['id']))
        user_profile = profile.json().get('profile')

        # check tag if exist
        # GET /repos/:owner/:repo/releases/tags/:tag
        url_check_tag = '{}/repos/{}/{}/releases/tags/{}'.format(URL_GIT, USER_GIT, __repo, __tag_name)
        check_tag = requests.get(url_check_tag, auth=HTTPBasicAuth(USER_GIT, PSWD_GIT))
        # if exist update tag
        if check_tag.status_code == 200:
            existing_tag_release = check_tag.json()
            # do update
            # PATCH /repos/:owner/:repo/releases/:release_id
            url_update_tag = '{}/repos/{}/{}/releases/{}'.format(URL_GIT, USER_GIT, __repo, existing_tag_release.get('id'))

            data_release = {
                "tag_name": __tag_name,
                "target_commitish": __commit_hash,
                "name": __tag_name,
                "body": "Update Release to {}".format(__tag_name),
                "draft": False,
                "prerelease": False,
            }

            patch_release = requests.patch(url_update_tag, data = json_dumps(data_release), auth = (USER_GIT, PSWD_GIT))

            # after update tag release we must update refs commit of tag
            # POST /repos/:owner/:repo/git/refs
            url_ref = "{}/repos/{}/{}/git/refs/tags/{}".format(URL_GIT, 'sendaljpt', 'slack-bot', __tag_name)
            data_ref = {
                "sha": __commit_hash,
                "force": True
            }
            patch_ref = requests.patch(url_ref, data = json_dumps(data_ref), auth = (USER_GIT, PSWD_GIT))

        
        # if not exist create new tag
        # POST /repos/:owner/:repo/releases
        elif check_tag.status_code == 404:
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

        message_slack = "{} tags {} with a commit {}".format(user_profile.get('email'), __tag_name, __commit_hash)
        await send_to_slack(channel=TO_CHANNEL, text=message_slack)

        return json({'message': 'Done!'})
    
    else:
        data = {
            "callback_id": "ryde-46e2b0",
            "title": "Taging github",
            "submit_label": "Submit",
            "state": "init",
            "elements": [
                {
                    "type": "text",
                    "label": "Repository",
                    "name": "repo"
                },
                {
                    "type": "text",
                    "label": "Commit Hash",
                    "name": "commit_hash"
                },
                {
                    "type": "text",
                    "label": "Tag Name",
                    "name": "tag_name"
                }
            ],
            "trigger_id": request.form.get('trigger_id')
        }
        
        
        client.dialog_open(dialog=data, trigger_id=request.form.get('trigger_id'))

        return json({'message': 'tag in progress'})


    # post_dialogue = requests.post('https://slack.com/api/dialog.open', data=json_dumps(data), headers=headers)

    # client.dialog_open(dialog=data, trigger_id=request.form.get('trigger_id'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2424)