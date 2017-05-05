import sys
import json
import requests
import time
import urllib
import string
#from dbhelper import DBHelper
import string
import random
import datetime
import tuber

# reserved for future db helper module
#db = DBHelper()

with open('config.json', 'r') as f:
    config = f.read()
    config_json = json.loads(config)

telegram_bot_token = config_json['telegram_bot_token']

URL = "https://api.telegram.org/bot{}/".format(telegram_bot_token)


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def send_message(text, chat_id, reply_markup=None, parse_mode=None):
    text = urllib.pathname2url(text.encode('utf-8'))
    url = URL + "sendMessage?text={}&chat_id={}" \
                "&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    if parse_mode:
        url += "&parse_mode={}".format(reply_markup)
    get_url(url)


def keyboard_remove():
    reply_markup = {"remove_keyboard": True}
    return json.dumps(reply_markup)


def process_message(update):
    telegram_uid = update["message"]["from"]["id"]
    chat_id = update["message"]["chat"]["id"]
    message = update["message"]["text"]
    
    if '/start' in message.lower() or \
        '/help' in message.lower():
        return 0

    count_message_words = len(message.split(' '))
    if count_message_words < 2:
        return 2

## TODO throttle requests
    t = tuber.YouTubeApi()
    
    url_comment_splitter = message.find(' ')
    video_url = message[:url_comment_splitter]
    
    response = t.get_video_params(video_url)
    
    if not response['success']:
        send_message(response['text'], chat_id)
        return None

    comment_text = message[url_comment_splitter+1:]
    
    response = t.post_comment(video_url, comment_text)
    
    if response['success']:
        send_message(response['text'], chat_id)
        return None
    else:
        send_message(response['text'], chat_id)
        return 1


def replies(reply_code):
    reply_dict = {
        0: 'In order to post a comment on youtube video, provide a link to the '
           'video followed by the comment. For example:\n'
           'https://www.youtube.com/watch?v=oHg5SJYRHA0 oh, no! not again!!',
        1: 'Please contact me @dooooooy',
        2: 'In order to post a comment on youtube video, provide a link to the '
           'video followed by the comment.'
    }
    return reply_dict[reply_code]


def handle_updates(updates):
    for update in updates["result"]:
        if not update.get("message"):
            continue
        elif not update.get("message").get("text"):
            continue
        chat_id = update["message"]["chat"]["id"]

        reply_code = process_message(update)
        
        if reply_code is not None:
            message = replies(reply_code)
            send_message(message, chat_id)


def main():
    last_update_id = None
    while True:
        # long polling testing indicator
        print("getting updates")
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
            time.sleep(0.5)


if __name__ == '__main__':
    main()
