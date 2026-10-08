""" Performs text transformation in English Idiom """


#### Setup ####
import re
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# personalized stopwords
PERSONALIZED_STOPWORDS = set(
    {
        "i",
        "me",
        "my",
        "myself",
        "we",
        "our",
        "ours",
        "ourselves",
        "you",
        "you're",
        "you've",
        "you'll",
        "you'd",
        "your",
        "yours",
        "yourself",
        "yourselves",
        "he",
        "him",
        "his",
        "himself",
        "she",
        "she's",
        "her",
        "hers",
        "herself",
        "it",
        "it's",
        "its",
        "itself",
        "they",
        "them",
        "their",
        "theirs",
        "themselves",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "that'll",
        "these",
        "those",
        "am",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "doing",
        "a",
        "an",
        "the",
        "and",
        "but",
        "if",
        "or",
        "because",
        "as",
        "until",
        "while",
        "of",
        "at",
        "by",
        "for",
        "with",
        "about",
        "against",
        "between",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "to",
        "from",
        "up",
        "down",
        "in",
        "out",
        "on",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "any",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "s",
        "t",
        "can",
        "will",
        "just",
        "don",
        "don't",
        "should",
        "should've",
        "now",
        "d",
        "ll",
        "m",
        "o",
        "re",
        "ve",
        "y",
        "ain",
        "aren",
        "aren't",
        "couldn",
        "couldn't",
        "didn",
        "didn't",
        "doesn",
        "doesn't",
        "hadn",
        "hadn't",
        "hasn",
        "hasn't",
        "haven",
        "haven't",
        "isn",
        "isn't",
        "ma",
        "mightn",
        "mightn't",
        "mustn",
        "mustn't",
        "needn",
        "needn't",
        "shan",
        "shan't",
        "shouldn",
        "shouldn't",
        "wasn",
        "wasn't",
        "weren",
        "weren't",
        "won",
        "won't",
        "wouldn",
        "wouldn't",
        "there",
        "and",
        "isn’t",
        "are",
        "and/or",
        "_and_",
        "s",
    }
)


# *** Regex Definitions ***
emails = re.compile(r"[\w\._]+@[^\s]+")
web_sites = re.compile(r"(http|https|www)+(://)?[^\s]+")
social_networks = re.compile(r"[^\w](@)[^\s]\w*\W?")
mark = re.compile(r"\w+\s?(™|®|©)")
mark_with_space = re.compile(r"\w+\s(©|®|™)")
date_full = re.compile(
    r"((\bjan|\bfeb|\bmar|\bmay|\bapr|\bjun|\bjul|\baug|\bsep|\boct|\bnov| \
    \bdec)+[\w]*)[\s\,\.\d]*[\s\W]*\d{1,4}(th|nd|st|rd)?"
)
date_day = re.compile(r"\d+\s?(days|day)")
date_in = re.compile(
    r"(in|on|of|from|to|till|between|and|at|since)\s?(\d{4}|_date_full_)"
)
full_numeric_date = re.compile(r"\d{2}[\-\/\s\.]\d{2}[\-\/\-\.]\d{2,4}")
hours_am_pm = re.compile(r"[\d\:]+\s?(am|pm)")
hours_numbers = re.compile(r"\d{1,2}:\d{1,2}:\d+")
measurements = re.compile(
    r"\d+[-\.\,]*\d*[\.\,]?\d*[m|½]?\s?(°c|oz|gsm|mil|degrees|degree|ml|mah|km²|km|-inch|mp| \
    gb|km|tonnes|tonnes|ton|oz|mm|g\/m|kilowatts|kilowatt|megawatts|megawatt|kg|k|million tons \
    |million ton|m2|m3)"
)
telephone = re.compile(
    r"(call|tel|phone|telephone)\s?[\+\-\s]\d+[\+\-\,\.\-\d]+")
money = re.compile(
    r"(us|us\$|\$|\£|\$\s|us\$|us\$|usd|€|\s)+\d+[.,\d+\s]\d*\s*(dollars|dollar|mi|bi|tri|quadri)+(llion\b|llions\b)?"
)
money_numbers = re.compile(
    r"(us|us\$|\$|\£|\$\s|us\$|us\$|usd|€)\d+[\.\,]*\d*(bn|m)?")
percentuals = re.compile(
    r"\d+[^\w]?\d*[^\w]?(\%|percentual|percent|percent| per cent)")
square_foot = re.compile(
    r"\s+\d+[\.\,]*\d*(-acre|acre|-square-foot|square-foot|-square foot|square foot)"
)
symbol_and = re.compile(r"\w+\s?\&\s?\w+")
numbers = re.compile(r"(\d+)[^\s\$](\d+)")
time = re.compile(r"\d+(\s?(\bmin|\bsec|\bhour)\w*)+")
sequences_of_underline = re.compile(r"[^\w](_)\1+[^\w]")
sequences_of_spaces = re.compile(r"[^\w](⠀)\1+[^\w]")

# Remove text between parenthesis or brackets
parenthesis = re.compile(r"\(([^)]*)\)")
brackets = re.compile(r"\[([^*\]]*)\]")

# remove pucntuation -> remove pucntuation that remained after the entire pre-process
apostrophes = re.compile(r"[\'|\’]")  # contractions
generic_symbols = re.compile(
    r'[\.|,|\¨|>|”|“|"|¨|\`|\´|—|\;|\:|?|/|=|>|<|+|\&|-|!|\‘|$|%|*|#|\\[|\\]'
)
final_numbers = re.compile(r"\s?\d+\s?")
symbols_preceeded_followed_by_space = re.compile(r"(\s\W\s)+")

STOPWORDS = stopwords.words("english")


def _get_stopwords():
    """ Access the stopwords in English

    Returns:
        [set]: Stopwords
    """
    stopwords = set(STOPWORDS)
    return stopwords.union(PERSONALIZED_STOPWORDS)


def remove_stopwords(string):
    """ Remove all stopwords words (link words that generally don't add value to the text)

    Args:
        string (str)

    Returns:
        [str]: Processed words
    """
    stopwords = _get_stopwords()
    return " ".join([t for t in word_tokenize(string) if t not in stopwords])


def remove_punctuation(string):
    """ Removes all punctuation variations defined in regex

    Args:
        string (str)

    Returns:
        [str]: Text without punctuation
    """
    string = square_foot.sub(" ", string)
    string = string.replace(" ", " ")
    string = apostrophes.sub(" ", string)
    string = emails.sub(" ", string)
    string = web_sites.sub(" ", string)
    string = social_networks.sub(" ", string)
    string = mark.sub(" ", string)
    string = mark_with_space.sub(" ", string)
    string = percentuals.sub(" ", string)
    string = string.replace("%", " ")
    string = measurements.sub(" ", string)
    string = hours_am_pm.sub(" ", string)
    string = hours_numbers.sub(" ", string)
    string = money.sub(" ", string)
    string = telephone.sub(" ", string)

    string = full_numeric_date.sub(" ", string)
    string = date_full.sub(" ", string)
    string = date_day.sub(" ", string)
    string = date_in.sub(" ", string)

    string = numbers.sub(" ", string)
    string = parenthesis.sub(" ", string)
    string = brackets.sub(" ", string)

    string = generic_symbols.sub(" ", string)
    string = final_numbers.sub(" ", string)
    string = symbols_preceeded_followed_by_space.sub(" ", string)

    string = sequences_of_underline.sub(" ", string)
    string = sequences_of_spaces.sub("", string)
    string = string.replace("-", " ")
    string = string.replace("_", " ")
    return string


def remove_length_1_tokens(string):
    """ Removes tokens with size less than 2

    Args:
        string (str)

    Returns:
        [str]: Processed string
    """
    return " ".join([x for x in word_tokenize(string) if len(x) > 1])


def text_lemmatizer(string):
    """Reduce words to their radicals

    Args:
        string (str): Each cleaned textual row from a Dataframe

    Returns:
        [str]: Lemmatized words in sentence
    """
    lemmatizer = WordNetLemmatizer()
    tokens = [w for w in string.split()]
    lemmatized = [lemmatizer.lemmatize(w) for w in tokens]
    
    return " ".join(lemmatized)