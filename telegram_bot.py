from telegram import Update
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler
from . import database
import os
import json
import datetime

env = os.environ
admin_list: list = json.loads(env["TGB_ADMINIDLIST"]) # [[id, username],......]

async def create_sublist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_sender.id in [telegram_information[0] for telegram_information in admin_list]:
        if (context.args) == 3:
            if context.args[1].isdigit():
                username: str = context.args[0]
                times: int = int(context.args[1])
                election_type: str = context.args[2]
                if context[3] == "now":
                    time: str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
                else:
                    time: str = context[3]
                new_sublist_information: list = database.LocalList.create_a_sublist(username, times, election_type, time)
                if -1 not in new_sublist_information and -2 not in new_sublist_information:
                    election_id: int = new_sublist_information
                    await context.bot.send_message(
                        chat_id= update.effective_chat.id,
                        reply_to_message_id= update.effective_message.message_id,
                        text= "已建立子列表，election_id为：" + str(election_id)
                    )
                else:
                    await context.bot.send_message(
                        chat_id= update.effective_chat.id,
                        reply_to_message_id= update.effective_message.message_id,
                        text= "发生未知错误，请与维护者联系。"
                    )
            else:
                await context.bot.send_message(
                    chat_id= update.effective_chat.id,
                    reply_to_message_id=update.effective_message.message_id,
                    text= "次数不正确。"
                )         
        else:
            await context.bot.send_message(
                chat_id= update.effective_chat.id,
                reply_to_message_id= update.effective_message.message_id,
                text= "您所传入参数之数量不正确。"
            )
    else:
        await context.bot.send_message(
            chat_id= update.effective_chat.id,
            reply_to_message_id= update.effective_message.message_id,
            text= "您无权使用此功能"
        )

# Testing
if __name__  == '__main__':
    application = ApplicationBuilder().token(env["TGB_TOKEN"]).build()
    create_handler = CommandHandler('create', create_sublist)
    application.add_handler(create_handler)
    application.run_polling()
    