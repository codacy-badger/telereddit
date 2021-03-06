import traceback

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from sentry_sdk import capture_exception
from config import MAX_TRIES

import reddit
import helpers


def send_random_posts(bot, chat_id, text):
    '''
    Searches the text for subreddit names and sends a random post from that
    subreddit.
    '''
    subreddits = helpers.get_subreddit_names(text)
    for subreddit in subreddits:
        tries = 0
        while tries < MAX_TRIES:
            status, err_msg = send_post(bot, chat_id, subreddit)
            if status == 'success':
                break
            tries += 1
        if status != 'success':
            _send_exception_message(bot, chat_id, err_msg)


def send_post_from_url(bot, chat_id, post_url):
    '''Sends the post from the given url.'''
    status, err_msg = send_post(bot, chat_id, post_url=post_url)
    if status != 'success':
        _send_exception_message(bot, chat_id, err_msg)


def send_post(bot, chat_id, subreddit=None, post_url=None):
    '''
    Sends a random post from the given subreddit if not None, sends the post
    from post_url otherwise.
    '''
    post, status, err_msg = reddit.get_post(subreddit, post_url)
    if status == 'not_found':
        bot.sendMessage(chat_id, err_msg)
    elif status != 'success':
        return status, err_msg

    try:
        # if it is not a random post (e.g. shared via link) don't show the edit
        # custom keyboard
        if post_url:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(text="Show another one", callback_data="more")
            ]])
        else:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(text="↻", callback_data="edit"),
                InlineKeyboardButton(text="✓", callback_data="send")
            ]])
        if 'www.youtube.com' in post.media_url:
            bot.sendMessage(chat_id, f"I'm sorry, youtube videos are not"
                            "supported yet :(", parse_mode='Markdown')
            return 'success', None

        if '/comments/' in post.content_url:
            # check if the post is a text post
            bot.sendMessage(chat_id, text=post.msg,
                            parse_mode='Markdown', reply_markup=keyboard,
                            disable_web_page_preview=True)
        elif post.media_type == 'gif':
            bot.sendDocument(chat_id, post.media_url, caption=post.msg,
                             parse_mode='Markdown', reply_markup=keyboard,
                             disable_web_page_preview=True)
        elif post.media_type == 'video':
            bot.sendVideo(chat_id, post.media_url, caption=post.msg,
                          parse_mode='Markdown', reply_markup=keyboard,
                          disable_web_page_preview=True)
        else:
            bot.sendPhoto(chat_id, post.media_url, caption=post.msg,
                          parse_mode='Markdown', reply_markup=keyboard,
                          disable_web_page_preview=True)

    except Exception as e:
        capture_exception(e)
        traceback.print_exc()
        return 'retry', "I'm sorry, an error occurred in sending the post"\
            " :(\nThe developer must have missed an if statement!"

    return 'success', None


def edit_result(bot, update):
    '''
    Edits the given message with a new post from that subreddit, and edits the
    keyboard markup to give the user the ability to edit or confirm the message.
    '''
    message = update.effective_message
    chat_id = message.chat_id
    message_id = message.message_id
    text = (message.caption or message.text) + '\n'
    subreddit = helpers.get_subreddit_name(text)
    if subreddit is None:
        return

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(text="↻", callback_data="edit"),
        InlineKeyboardButton(text="✓", callback_data="send")
    ]])
    tries = 0
    while tries < MAX_TRIES:
        post, status, err_msg = reddit.get_post(subreddit)
        if status != 'success':
            continue
        if '/comments/' not in post.content_url and message.caption is not None:
            media = InputMediaPhoto(post.content_url, post.msg, 'Markdown')
            bot.editMessageMedia(chat_id, message_id, media=media,
                                 reply_markup=keyboard)
            break
        elif '/comments/' in post.content_url and message.caption is None:
            bot.editMessageText(post.msg, chat_id, message_id,
                                parse_mode='Markdown', reply_markup=keyboard,
                                disable_web_page_preview=True)
            break
        tries += 1

    if tries >= MAX_TRIES:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(text="Retry  ↻", callback_data="edit"),
            InlineKeyboardButton(text="✓", callback_data="send")
        ]])
        bot.editMessageReplyMarkup(chat_id, message_id, reply_markup=keyboard)


def _send_exception_message(bot, chat_id, msg):
    '''Handles the errors created in post retrieval and sending.'''
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Try with another random post', callback_data='more')]
    ])
    bot.sendMessage(chat_id, msg, 'Markdown', reply_markup=keyboard)
