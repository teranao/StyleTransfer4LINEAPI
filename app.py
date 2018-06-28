# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import errno
import os
import sys
import tempfile
from argparse import ArgumentParser

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction, FlexSendMessage,
    CarouselTemplate, CarouselColumn, PostbackEvent, ImageComponent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage, BubbleContainer,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent, ImageSendMessage
)

from run_test import style

from PIL import Image

app = Flask(__name__)

line_bot_api = LineBotApi(
    "o1Pv6P2aX5mKfn9llnkoOw2EKauNWYVeoWZ20kTMeP5I83airwGE1gjlVaYkb+jUTt+c1623mMu0FMK+QNSjH7P2Ua8k+cGKzS4sKrFVDQ4E5W1TVnlJj+Mi/LaeFOy9UFtDk374dpLrXbrrYJOPuwdB04t89/1O/w1cDnyilFU=")
handler = WebhookHandler("f66aade52ceefbb6e5cf48bdc9a1a625")

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

base_url = "https://nayopu.ngrok.io/"

styles = {
    "la muse": "la_muse",
    "princess": "rain_princess",
    "scream": "the_scream",
    "shipwreck": "shipwreck",
    "udnie": "udnie",
    "wave": "wave",
}

class UserStatus():
    def __init__(self):
        self.state = "waiting"
        self.coord = []
        self.isexplained = False

    def clear(self):
        self.state = "waiting"
        self.coord = []


# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text

    if text == "ばいばい":
        if isinstance(event.source, SourceGroup):
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text='サヨウナラ'))
            line_bot_api.leave_group(event.source.group_id)
        elif isinstance(event.source, SourceRoom):
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text='サヨウナラ'))
            line_bot_api.leave_room(event.source.room_id)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Bot can't leave from 1:1 chat"))




@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_content_message(event):
    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    elif isinstance(event.message, VideoMessage):
        ext = 'mp4'
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
    else:
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    # get path
    dist_path = tempfile_path + '.' + ext
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)
    image_path = os.path.join('static', 'tmp', dist_name)

    # list of ImageCarouselColumn
    clist = []
    for label, model in styles.items():
        clist.append(
            ImageCarouselColumn(
                image_url=base_url+os.path.join('static', 'style_thumb', model+".jpg"),
                action=PostbackAction(label=label, data=model+" "+dist_name, text=label)
            )
        )

    image_carousel_template = ImageCarouselTemplate(columns=clist)

    template_message = TemplateSendMessage(
        alt_text='ImageCarousel alt text', template=image_carousel_template)
    line_bot_api.reply_message(event.reply_token, template_message)


@handler.add(PostbackEvent)
def handle_postback(event):
    # split postback data
    model, dist_name = event.postback.data.split()
    output_image = model+dist_name

    image_path = os.path.join('static', 'tmp', dist_name)

    output_path = os.path.join('static', 'output', output_image)
    thumb_path = os.path.join('static', 'thumb', output_image)


    # style taransfer
    style(
        content=image_path,
        output=output_path,
        style_model=os.path.join('models', model+".ckpt")
    )

    # create thumbnail
    img = Image.open(output_path)
    img.thumbnail((240, 240))
    img.save(thumb_path)

    # reply
    line_bot_api.reply_message(event.reply_token, ImageSendMessage(
        original_content_url=base_url+output_path,
        preview_image_url=base_url+thumb_path
    ))


if __name__ == "__main__":
    arg_parser = ArgumentParser(usage='Usage: python ' + __file__ + ' [--port <port>] [--help]')
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=True, help='debug')
    options = arg_parser.parse_args()

    # create tmp dir for download content
    make_static_tmp_dir()

    app.run(debug=options.debug, port=options.port)
