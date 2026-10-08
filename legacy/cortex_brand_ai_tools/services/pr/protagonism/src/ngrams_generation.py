""" Implements the cortex methodology for protagonism classification """

#### Setup ####
import math
from services.pr.text_treatment import find_ngrams


def ngrams_from_words(word_list):
    """Generate Ngrams from the word list

    Args:
        word_list (list)

    Returns:
        [dict]: Dictionary with slices from word list (with original words and ngrams)
    """

    counter_words = find_ngrams.find_ngrams_counter(word_list)
    counter_words.sort(key=lambda tup: tup[1], reverse=True)
    len_words = len(counter_words)

    words_frequency_slices = {}

    maximum = 0.08
    minimum = 0.01
    most_frequently_size = math.floor(len_words * maximum)
    medium_frequently_size = math.floor((len_words * minimum))

    most_common_words = counter_words[0:most_frequently_size]
    medium_common_words = counter_words[most_frequently_size:medium_frequently_size]
    less_common_words = counter_words[medium_frequently_size:]

    formatted_most_common = {}
    formatted_medium_common = {}
    formatted_less_common = {}

    for term, freq in most_common_words:
        formatted_most_common[" ".join(term)] = freq
    for term, freq in medium_common_words:
        formatted_medium_common[" ".join(term)] = freq
    for term, freq in less_common_words:
        formatted_less_common[" ".join(term)] = freq

    words_frequency_slices['slice_one'] = " ".join(
        formatted_most_common.keys())
    words_frequency_slices['slice_two'] = " ".join(
        formatted_medium_common.keys())
    words_frequency_slices['final_slice'] = " ".join(
        formatted_less_common.keys())

    return words_frequency_slices


def ngrams_from_title(title):
    """Generate Ngrams news title

    Args:
        title (str)

    Returns:        
        [str]: Formated title with ngrams
    """
    return find_ngrams.find_ngrams_in_protagonism_text(title)

    
def ngrams_from_slices(slices):
    """Generate Ngrams from the news body

    Args:
        word_list (dict): {'slice_one': ['all words']}        

    Returns:
        [dict]: Dictionary with slices  (with original words and ngrams)
        [str]: Formated title with ngrams
    """
    ngrams_slices = {}
    ngrams_slices['slice_one'] = find_ngrams.find_ngrams_in_protagonism_text(
        slices['slice_one'])
    ngrams_slices['slice_two'] = find_ngrams.find_ngrams_in_protagonism_text(
        slices['slice_two'])
    ngrams_slices['final_slice'] = find_ngrams.find_ngrams_in_protagonism_text(
        slices['final_slice'])
    

    return ngrams_slices
