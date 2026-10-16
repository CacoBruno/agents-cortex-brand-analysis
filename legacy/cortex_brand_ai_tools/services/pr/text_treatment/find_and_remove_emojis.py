import re
from services.pr.text_treatment import emojis_unicodes

PATTERN = emojis_unicodes.get_emojis_unicodes()
EMOJI_PATTERN = re.compile(PATTERN)

def remove_emojis_from_str(string):
    """Receives a string and remove emojis

    Args:
        string (str): Text that contains emojis

    Returns:
        [str]: Text with emojis properly removed
    """
    return " ".join([w for w in string.split() if EMOJI_PATTERN.search(w) is None])


def get_emojis_from_str(string):
    """Finds all emojis from string

    Args:
        string (str)

    Returns:
        [str]
    """
    return " ".join([w for w in string.split() if EMOJI_PATTERN.search(w) is not None])


def removing_emojis_from_sentences(string, list_of_emojis_in_text):
    """Removes all emojis in sentences

    Args:
        string (str): Each textual row from a DataFrame
        list_of_emojis_in_text (set): Set of emojis found in
        a corpus (collection of documents, all training dataframe)

    Returns:
        string (str): Cleaned sentence
    """
    for emoji in list_of_emojis_in_text:
        if emoji in string:
            string = string.replace(emoji, "")
    return string


def find_emojis_in_dataframe(dataframe, column):
    """Find all emojis in a DataFrame (read unicode patters from a file)

    Args:
        dataframe (Dataframe): Which has a text column where we'll look for emojis for removal
        column (str): Dataframe text column

    Returns:
        list_of_emojis_in_text (set): set of all emojis
    """
    sentences = dataframe[column].to_string(index=False)
    list_of_emojis_in_text = set()
    for word in sentences.split():
        emoji_finder = EMOJI_PATTERN.search(word)
        if emoji_finder:
            list_of_emojis_in_text.add(emoji_finder.group(0))
    return list_of_emojis_in_text
