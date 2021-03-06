#!/usr/bin/env python
import sentry_sdk

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, CallbackQueryHandler, Filters
import logging

from secret import TELEGRAM_TOKEN, SENTRY_TOKEN
import reddit_linker
import helpers


def on_chat_message(bot, update):
    '''Handles a single update message.'''
    msg = update.message
    if not msg.text:
        return
    if any(r in msg.text.lower() for r in ['reddit.com', 'redd.it']):
        posts_url = helpers.get_urls_from_text(msg.text)
        for url in posts_url:
            reddit_linker.send_post_from_url(bot, msg.chat_id, url)
    elif 'r/' in msg.text.lower():
        reddit_linker.send_random_posts(bot, msg.chat_id, msg.text)


def on_callback_query(bot, update):
    '''Handles all the several types of callback queries.'''
    query_id = update.callback_query.id
    query_data = update.callback_query.data
    message = update.effective_message
    chat_id = message.chat_id
    message_id = message.message_id
    text = (message.caption or message.text) + '\n'

    if query_data == 'more':
        # upon clicking the "more" button, send another random reddit post
        subreddit = helpers.get_subreddit_name(text)
        if subreddit is not None:
            reddit_linker.send_random_posts(bot, chat_id, subreddit)
    elif query_data == 'send':
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(text="Show another one", callback_data="more")
        ]])
        bot.editMessageReplyMarkup(chat_id, message_id, reply_markup=keyboard)
    elif query_data == 'edit':
        reddit_linker.edit_result(bot, update)

    bot.answerCallbackQuery(query_id)


if __name__ == "__main__":
    sentry_sdk.init(SENTRY_TOKEN)

    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    dispatcher.add_handler(MessageHandler(Filters.text, on_chat_message))
    dispatcher.add_handler(CallbackQueryHandler(on_callback_query))
    updater.start_polling()
