from flask import Flask, request, abort
from mybot import app, db
from mybot.models import Room, User
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
        title='待ち合わせ日時',
        text='いつ集まりますか？',
        actions=[
            DatetimePickerAction(
                label='設定する',
                data='hoge=1', 
                mode='datetime'
            ),
        ]
        )
    )

    return buttons_template_message

def make_time_str(time):
    
    h = time // 3600
    m = time // 60
    s = int(time % 60)

    time_str = ""

    if h > 0:
        time_str += str(h) + "時間"
    
    if m > 0:
        time_str += str(m) + "分"

    if s > 0:
        time_str += str(s) + "秒"

    return time_str

def judgeTime(meeting_time, user_time):
    msgs = []
    time_diff = abs(meeting_time - user_time)
    time_str = make_time_str(time_diff)

    if meeting_time < user_time:
        msgs.append(TextSendMessage(text='遅刻'))        
        msgs.append(TextSendMessage(text='超過時間は'+time_str))
    elif meeting_time == user_time:
        msgs.append(TextSendMessage(text='ジャスト'))

    elif meeting_time > user_time:
        msgs.append(TextSendMessage(text='順調'))
        msgs.append(TextSendMessage(text='待ち合わせまであと'+time_str))

    return msgs

@handler.add(MessageEvent)
def handle_message(event):
    group_id = event.source.group_id if event.source.type == "group" else event.source.room_id
    room = Room.query.filter_by(group_id=group_id).first()
    if event.message.text == "設定":
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

    elif event.message.text == "結果" and (room.time is not None):
        message = ""
        users = User.query.order_by(User.rank).all()

        if not users:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text= "結果はまだわからない！！")
            )
            
        else:
            for user in users:
                message += str(user.rank) + "位は" + user.name + "さん！\n"

            start = users[0].arrive_time.timestamp()
            end = users[-1].arrive_time.timestamp()
            message += "全員が集まるまでにかかった時間はなんと\n"+ make_time_str(end-start) + "\n"

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text= message + "お疲れ様でした。失礼します。")
            )
            for user in room.users:
                db.session.delete(user)
                db.session.commit()

            db.session.delete(room)
            db.session.commit()
            line_bot_api.leave_group(event.source.group_id)
    
    elif event.message.text == "ついた" and (room.time is not None):
        profile = line_bot_api.get_profile(event.source.user_id)
        msgs = []
        user = User.query.filter_by(user_id=profile.user_id).first()

        if user is None:
            user = User(user_id=profile.user_id, name=profile.display_name, rank=len(room.users)+1, room=room, arrive_time = datetime.datetime.fromtimestamp(event.timestamp / 1000))
            msgs.append(TextSendMessage(text="おおっと、"+user.name+"さんが到着しました！\n順位は"+str(user.rank)+"位だ！")
)
            msgs += judgeTime(room.time.timestamp(), (event.timestamp)/1000)

        else:
            msgs.append(TextSendMessage(text="すでに到着しているぅ！\n集合したら「結果」をお願いします！"))

        db.session.add(user)
        db.session.commit()
        line_bot_api.reply_message(
                event.reply_token,
                msgs
                )
        
    else:
        if room.time is None:
            message = "待ち合わせ実況botです。\n"+"「設定」で待ち合わせ時間をグループに知らせてください"
        else:
            user_time = event.timestamp / 1000
            meeting_time = room.time.timestamp()
            message = judgeTime(meeting_time, user_time)
            line_bot_api.reply_message(
	        event.reply_token,
		message
            )

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
    msg.append(TextSendMessage(text="待ち合わせ実況botです。\n"+"「設定」で待ち合わせ時間をグループに知らせてください")
            )
    #msg.append(TextSendMessage(text=event.source.group_id))
    room = Room.query.filter_by(group_id=event.source.group_id).first()
    if room is None:
        room = Room(group_id=event.source.group_id) 
    
    db.session.add(room)
    db.session.commit()
    #msg.append(TextSendMessage(text="GroupIdを保存しました"))

    line_bot_api.reply_message(
            event.reply_token,
            msg
            )

if __name__ == "__main__":
    #    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
