from flask import Flask, request, abort
from mybot import app, db
from mybot.models import Room
import datetime

from linebot import (
        LineBotApi, WebhookHandler
        )
from linebot.exceptions import (
        InvalidSignatureError
        )
from linebot.models import (
        MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageAction, DatetimePickerAction, PostbackEvent, JoinEvent
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
        room = Room.query.filter_by(group_id=event.source.group_id).first()
        if room.time is None:
            button = make_time_button()
            line_bot_api.reply_message(
                    event.reply_token,
                    button 
                    )
        else:
            line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="待ち合わせは"+str(room.time)+"です") 
                    )

    elif event.message.text == "結果":
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="お疲れ様でした。失礼します。")
                )
        room = Room.query.filter_by(group_id=event.source.group_id).first()
        db.session.delete(room)
        db.session.commit()
        line_bot_api.leave_group(event.source.group_id)

@handler.add(PostbackEvent)
def handler_PostbackEvent(event):
    pick_time = event.postback.params["datetime"]
    room = Room.query.filter_by(group_id=event.source.group_id).first()
    room.time = datetime.datetime.strptime(pick_time, '%Y-%m-%dT%H:%M')
    db.session.add(room)
    db.session.commit()

    line_bot_api.reply_message(
    event.reply_token,
    TextSendMessage(text="待ち合わせ日時は"+pick_time+"に設定しました")
    )    

@handler.add(JoinEvent)
def handle_join(event):
    msg = []
    msg.append(TextSendMessage(text="こんにちは"))
    msg.append(TextSendMessage(text=event.source.group_id))
    room = Room.query.filter_by(group_id=event.source.group_id).first()
    if room is None:
        room = Room(group_id=event.source.group_id) 
    
    db.session.add(room)
    db.session.commit()
    msg.append(TextSendMessage(text="GroupIdを保存しました"))

    line_bot_api.reply_message(
            event.reply_token,
            msg
            )

if __name__ == "__main__":
    #    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
