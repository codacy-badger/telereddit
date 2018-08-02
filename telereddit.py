#!/usr/bin/env python
import time
import telepot

from secret import TELEGRAM_TOKEN as TOKEN
import reddit_linker


# handle chat messages
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    text = msg['text']
    if content_type == 'text' and 'r/' in text.lower():
        reddit_linker.send_link(bot, chat_id, text)


# handle inline keyboard
def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    if query_data == 'reddit':
        reddit_linker.more_button_callback(bot, msg)
    bot.answerCallbackQuery(query_id)


# main function
def main():
    bot.message_loop({'chat': on_chat_message, 'callback_query': on_callback_query})

    # Keep the program running
    while 1:
        time.sleep(3)


bot = telepot.Bot(TOKEN)

if __name__ == "__main__":
    main()