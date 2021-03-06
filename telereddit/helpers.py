import re
from config import MAX_TITLE_LENGTH


def get_subreddit_names(text):
    '''
    Returns a list of the (prefixed) subreddit names present in the given text.
    '''
    regex = r'r/[A-Za-z0-9][A-Za-z0-9_]{2,20}(?=\s|\W |$|\W$|/)'
    return re.findall(regex, text, re.MULTILINE)


def get_subreddit_name(text):
    '''
    Returns the first (prefixed) subreddit name if present in the given text,
    None otherwise.
    '''
    subs = get_subreddit_names(text)
    if len(subs):
        return subs[0]
    else:
        return None


def escape_markdown(text):
    '''
    Returns the given text with escaped common markdown characters.
    '''
    return text.replace('*', '\\*').replace('_', '\\_')


def truncate_text(text, length=MAX_TITLE_LENGTH):
    '''
    Returns the given text, truncated at `length` characters, plus ellipsis.
    '''
    return text[:length] + (text[length:] and '...')


def polish_text(text):
    '''
    Returns the given text without newline characters.
    '''
    return text.replace('\n', ' ')


def get_urls_from_text(text):
    '''
    Returns a list of the urls present in the given text.
    '''
    polished = polish_text(text)
    urls = list()
    for w in polished.lower().split(' '):
        if 'reddit.com' in w:
            urls.append(w.partition('/?')[0] + '.json')
        if 'redd.it' in w:
            urls.append(f'https://www.reddit.com/comments/{w.partition("redd.it/")[2]}.json')
    return urls


def get(obj, attr, default=None):
    '''
    Returns the value `attr` if it is not None, default otherwise.
    '''
    return obj[attr] if attr in obj and obj[attr] is not None else default


def chained_get(obj, attrs, default=None):
    '''
    Travels the nested object based on `attrs` and returns the value of the
    last attr if not None, default otherwise.
    '''
    for attr in attrs:
        obj = get(obj, attr, default)
        if obj == default:
            break
    return obj
