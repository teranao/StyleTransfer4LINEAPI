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

    bubble = BubbleContainer(
        hero=ImageComponent(
            url='https://nayopu.ngrok.io/style/apple.jpg',
            size='full',
            aspect_ratio='20:13',
            aspect_mode='cover',
            action=MessageAction(label='wave', text="wave")
        )
    )

    message = FlexSendMessage(alt_text="Which image do you like?", contents=bubble)
    line_bot_api.reply_message(
        event.reply_token,
        message
    )


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

    style_image = {

    }
    carousel = CarouselTemplate(columns=[
        BubbleContainer(
            hero=ImageComponent(
                url='https://nayopu.ngrok.io/style/apple.jpg',
                size='full',
                aspect_ratio='20:13',
                aspect_mode='cover',
                action=MessageAction(label='wave', text="wave")
            )
        )]
    )

    template_message = TemplateSendMessage(
        alt_text='Carousel alt text', template=carousel
    )
    line_bot_api.reply_message(
        event.reply_token,
        template_message
    )

    # style taransfer
    style(content=image_path, output=os.path.join('static', 'output', dist_name), style_model="models/wave.ckpt")

    # create thumbnail
    img = Image.open(os.path.join('static', 'output', dist_name))
    img.thumbnail((240, 240))
    img.save(os.path.join('static', 'thumb', dist_name))

    # reply
    base_url = "https://ebc4b394.ngrok.io/"
    line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=base_url+os.path.join('static', 'output', dist_name), preview_image_url=base_url+os.path.join('static', 'thumb', dist_name)))

    # line_bot_api.reply_message(

    # event.reply_token, [
    #    TextSendMessage(text='Save content.'),
    #    TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
    # ])

    # style(content="content/cockatoo.jpg", output="result.jpg", style_model="models/wave.ckpt")


if __name__ == "__main__":
    arg_parser = ArgumentParser(usage='Usage: python ' + __file__ + ' [--port <port>] [--help]')
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=True, help='debug')
    options = arg_parser.parse_args()

    # create tmp dir for download content
    make_static_tmp_dir()

    # create user stats dictionary
    global user_dict
    user_dict = {}

    app.run(debug=options.debug, port=options.port)
