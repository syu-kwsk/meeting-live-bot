from flask import Flask, request, abort
from mybot import app

from linebot import (
        LineBotApi, WebhookHandler
        )
from linebot.exceptions import (
        InvalidSignatureError
        )
from linebot.models import (
        MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageAction, DatetimePickerAction, PostbackEvent
        )
import os
import random

#環境変数取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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

def make_time_button():
    buttons_template_message = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
        thumbnail_image_url='https://1.bp.blogspot.com/-RJRt_Hv37Kk/VMIu-CCBpII/AAAAAAAAq2E/JsIJ8pPwmuY/s400/calender_takujou.png',
        title='Meeting Time',
        text='Please select',
        actions=[
            DatetimePickerAction(
                label='pick date',
                data='hoge=1', 
                mode='datetime'
            ),
        ]
        )
    )

    return buttons_template_message

@handler.add(MessageEvent)
def handle_message(event):
    if event.message.text == "設定":
        button = make_time_button()
        line_bot_api.reply_message(
            event.reply_token,
            button 
        )

if __name__ == "__main__":
    #    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


