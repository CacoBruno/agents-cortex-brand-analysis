""" Performs text transformation """
import re
import unidecode
from bs4 import BeautifulSoup

from services.pr.text_treatment import text_processing_en, text_processing_pt
from services.pr.text_treatment.find_and_remove_emojis import remove_emojis_from_str

def remove_stopwords(string, language):
    """Remove all stopwords words (link words that generally don't add value to the text).
        Defines the specific role to solve this task based on language.

    Args:
        string (str)

    Returns:
        [str]: Processed words
    """
    if language == "en":
        return text_processing_en.remove_stopwords(string)
    if language == "pt":
        return text_processing_pt.remove_stopwords(string)
    return string


def remove_punctuation(string, language):
    """Removes all punctuation variations defined in regex based on language.
        Defines the specific role to solve this task based on language.
    Args:
        string (str)

    Returns:
        [str]: Text without punctuation
    """    
    if language == "en":
        return text_processing_en.remove_punctuation(string)
    if language == "pt":
        return text_processing_pt.remove_punctuation(string)
    return string


def remove_length_1_tokens(string, language):
    """Removes tokens with size less than 2.
        Defines the specific role to solve this task based on language.

    Args:
        string (str)

    Returns:
        [str]: Processed string
    """
    if language == "en":
        return text_processing_en.remove_length_1_tokens(string)
    if language == "pt":
        return text_processing_pt.remove_length_1_tokens(string)
    return string

def remove_length_2_tokens(string, language):
    """Removes tokens with size less than 2.
        Defines the specific role to solve this task based on language.

    Args:
        string (str)

    Returns:
        [str]: Processed string
    """
    if language == "en":
        return text_processing_en.remove_length_2_tokens(string)
    if language == "pt":
        return text_processing_pt.remove_length_2_tokens(string)
    return string


def text_lemmatizer(string, language):
    """Reduce words to their radicals.
        Defines the specific role to solve this task based on language.

    Args:
        string (str): Each cleaned textual row from a Dataframe

    Returns:
        sentenced: Lemmatized words in sentence
    """
    if language == "en":
        return text_processing_en.text_lemmatizer(string)
    if language == "pt":
        return text_processing_pt.text_lemmatizer(string)
    return string


def process_text_to_protagonism(string, language):
    if language == "pt":
        return text_processing_pt.clean_to_protagonism(string)


def remove_html_tags(string):
    """Remove HTML tags from text

    Args:
        s (str)

    Returns:
        [str]: Cleaned text
    """
    soup = BeautifulSoup(string, features="html.parser")
    return soup.get_text()


def remove_digits(string, language):    
    return text_processing_pt.remove_digits(string)

def remove_enrichment(string, language):    
    return text_processing_pt.remove_enrichment(string)

def remove_sequences_of_spaces(string, language):
    return text_processing_pt.remove_sequences_of_spaces(string)

def remove_specific_words(string, language):
    return text_processing_pt.remove_specific_words(string)

def clean_text(string, language, **kwargs):
    """

    Args:
        s (str): Raw text
        language (str): Acronym for the language (must be 'pt' or 'en')
        kwargs (list):  A list named as cleaning_tasks, must contain one or more options
                        according to the following nomenclature:
                        - html - used to remove html tags the text
                        - lower - used to lowercase conversion
                        - stopwords - used to remove stopwords
                        - punctuation -  used to remove punctuation
                        - emojis - used to remove emojis
                        - lemmatize - used to reduce words to their roots
                        - length_1 - used to remove letters lower than one character

    Returns:
        [str]: Cleaned text
    """

    cleaning_tasks = kwargs.get("cleaning_tasks")

    if language not in ["en", "pt"]:
        print(f"No specific cleaning for this language {language}")
        
    if "lower" in cleaning_tasks:        
        string = string.lower()
    if "stopwords" in cleaning_tasks:        
        string = remove_stopwords(string, language)                        
    if "punctuation" in cleaning_tasks:        
        string = remove_punctuation(string, language)
    if "digits" in cleaning_tasks:
        string = remove_digits(string, language)  
    if "sequences_of_spaces" in cleaning_tasks:
        string = remove_sequences_of_spaces(string, language)                      
    if "lemmatize" in cleaning_tasks:
        string = text_lemmatizer(string, language)     
    if "remove_enrichment" in cleaning_tasks:
        string = remove_enrichment(string, language)                           
    if "html" in cleaning_tasks:
        string = remove_html_tags(string)    
    if "emojis" in cleaning_tasks:
        string = remove_emojis_from_str(string)
    if "length_1" in cleaning_tasks:
        string = remove_length_1_tokens(string, language)
    if "length_2" in cleaning_tasks:
        string = remove_length_2_tokens(string, language)        
    if "specific_words" in cleaning_tasks:
        string = remove_specific_words(string, language)                
        

    return string.strip()


def replace_values_in_text(string, dictionary):
    """Searches the text for terms present in the dictionary values and replaces them with the keys.
        Used when dictionary values are ngrams.
    Args:
        string (str): Text
        dictionary (dict): Dictionary of terms where keys are the terms used to replace in text

    Returns:
        [str]: Text with terms replaced
    """

    dictionary = dict((re.escape(k), v) for k, v in dictionary.items())
    pattern = re.compile("|".join(dictionary.keys()))
    return pattern.sub(lambda x: dictionary[re.escape(x.group(0))], string)


def replace_protagonism_terms_in_text(string, dictionary):
    """Searches the text for terms present in the dictionary values and replaces them with the keys.
        Used in protagonism model because there are mentions such as br -> br distributor that,
        without the use of the regex, could be replaced in words such as 'BRasil' and 'coBRança'.

    Args:
        string (str): Text
        dictionary (dict): Dictionary of terms where keys are the terms used to replace in text

    Returns:
        [str]: Text with terms replaced
    """
    variations_to_replace = list(dictionary.keys())
    variations_to_replace = sorted(variations_to_replace, reverse=True)
    main_value = list(set(dictionary.values()))[0]
    pattern = "|".join(variations_to_replace)
    re_pattern = rf"\b(?:{pattern})\b"
    re_pattern = re.compile(re_pattern, re.S)
    return re.sub(re_pattern, main_value, string)


def truncate_text(string, max_length):
    """Defines an x length (max_length) of the sentence

    Args:
        string (str)
        max_length (int): Maximum sentence length

    Returns:
        [str]
    """
    return (
        " ".join(string[0:max_length].split()[:-1])
        if len(string) >= max_length
        else string
    )
