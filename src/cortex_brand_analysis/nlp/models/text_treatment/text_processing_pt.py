""" Performs text transformation in Portuguese Idiom """


#### Setup ####
import re
import string as s
import spacy
import unidecode
from nltk import word_tokenize
from nltk.corpus import stopwords

#---------------------
# Words to remove
#---------------------
VOWELS = ["a", "e", "i", "o", "u", "à", "é"]

WORDS_TO_REMOVE = [
    "https",
    "html",
    "www",
    "http",  
    "facebook",
    "instagram",
    "twitter",
    "gl", 
    "glb",
    'www',
    'bit',
    'ly',    
    'ddd'        
]

SPECIFIC_WORDS = ['sobre', 'dar', 'ser', 'de', 'do', 'dos', 'das',
                      'ja',
                    'tambem',
                    'sao',
                    'nao',
                    'ate',
                    'ja',
                  'alem', 'apos', 'ate', 'com', 'contra', 'desde', 'para', 'per',
                  'perante', 'por', 'sem', 'sob', 'sobre', 'tras', 'ainda', 'vai']
STOPWORDS = stopwords.words("portuguese")       

#---------------------
# Regex Definitions
#---------------------
punctuations = re.compile(r"[^\w\s]")
digits_pattern = re.compile(r'(\d)\w*')
sequences_of_spaces = re.compile(r"[ \t]{2,}")

def _get_stopwords():
    """ Access the stopwords in Portuguese

    Returns:
        [set]: Stopwords
    """
     
    stopwords = set(STOPWORDS)
    return stopwords.union(WORDS_TO_REMOVE)


def remove_stopwords(string):    
    """ Remove all stopwords words (link words that generally don't add value to the text)    

    Args:
        string (str)

    Returns:
        [str]: Processed words
    """
    stopwords = _get_stopwords()
    return " ".join(
        [t for t in word_tokenize(
            string, language="portuguese") if t not in stopwords and t not in VOWELS]
    )


def remove_specific_words(string):
    """_summary_

    Args:
        string (_type_): _description_

    Returns:
        _type_: _description_
    """
    
    return " ".join(
        [t for t in word_tokenize(
            string, language="portuguese") if t not in SPECIFIC_WORDS]
    )

def remove_punctuation(string):
    """ Removes all punctuation variations defined in regex

    Args:
        string (str)

    Returns:
        [str]: Text without punctuation
    """             
    string = "".join([word.lower() for word in string])            
    string = string.replace('\'', '')     
    string = string.replace('’', '')
    string = string.replace('``', '')        
        
    
    string = unidecode.unidecode(string)
    string = punctuations.sub(" ", string)                 
    string = sequences_of_spaces.sub(" ", string)    
    return string



def remove_sequences_of_spaces(string):
    """_summary_

    Args:
        string (_type_): _description_

    Returns:
        _type_: _description_
    """
    return sequences_of_spaces.sub(" ", string)   

def remove_digits(string):
    """_summary_

    Args:
        string (_type_): _description_

    Returns:
        _type_: _description_
    """
    return digits_pattern.sub(" ", string)


def remove_length_1_tokens(string):
    """ Removes tokens with size equal 1

    Args:
        string (str)

    Returns:
        [str]: Processed string
    """

    length_1_words_to_remove = [x for x in string.split(' ') if len(x) == 1]
    new_s = " ".join([x for x in string.split(' ')
                      if x not in length_1_words_to_remove])
    return new_s

def remove_length_2_tokens(string):
    """ Removes tokens with size equal 2

    Args:
        string (str)

    Returns:
        [str]: Processed string
    """

    length_1_words_to_remove = [x for x in string.split(' ') if len(x) == 2]
    new_s = " ".join([x for x in string.split(' ')
                      if x not in length_1_words_to_remove])
    return new_s



def text_lemmatizer(string):
    """Reduce words to their radicals

    Args:
        sentences (str): Each cleaned textual row from a Dataframe

    Returns:
        [str] Lemmatized words in sentence
    """
    nlp_pt = spacy.load("pt_core_news_sm", disable=[
                        "parser", "textcat", "tagger"])
    string = nlp_pt(string)
    lemmatized = " ".join([sent.lemma_ for sent in string])
    return lemmatized

def remove_enrichment(string):
    """_summary_

    Args:
        string (_type_): _description_

    Returns:
        _type_: _description_
    """
    if '_' in string:
        return string.replace('_', ' ')
    return string