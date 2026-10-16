""" Implements the cortex methodology for protagonism classification """

#### Setup ####
import re


def search_in_title(formatted_title, title, title_tokenize, variable):
    """Inspect if variable appears in title to determine the protagonism

    Args:
        formatted_title (str): Normalized title as text
        title (str): Original title
        title_tokenize (list): Normalized title as tokens ['token1', 'token2']
        variable (str): Value to search

    Returns:
        [bool]
    """
    variable_pattern = re.compile(rf"\b{variable}\b")

    if len(variable_pattern.findall(" ".join(formatted_title))) > 0 or \
            len(variable_pattern.findall(title)) > 0 or \
            len(variable_pattern.findall(" ".join(title_tokenize))) > 0:
        varibale_in_title = True
    else:
        varibale_in_title = False

    return varibale_in_title


def search_in_text_slices(ngrams_text_slices, variable):
    """Inspect variable position in text slices to determine protagonism

    Args:
        ngrams_text_slices (dict): Formatted text 
        variable (str): Value to search

    Returns:
        [dict]: Formatted as: {'position': Bool}
    """

    is_in_slice_one = False
    is_in_slice_two = False
    is_in_final_slice = False
    empty_text = False
    relevance_in_text_slices = {}

    ngrams_slice_one = " ".join(ngrams_text_slices['slice_one'])
    ngrams_slice_two = " ".join(ngrams_text_slices['slice_two'])
    ngrams_final_slice = " ".join(ngrams_text_slices['final_slice'])

    variable_pattern = re.compile(rf"\b{variable}\b")
    
    if len(ngrams_slice_one) != 0:
        if len(variable_pattern.findall(ngrams_slice_one)) > 0:
            is_in_slice_one = True
        else:
            is_in_slice_one = False
        empty_text = False

    if len(ngrams_slice_two) != 0:
        if len(variable_pattern.findall(ngrams_slice_two)) > 0 and len(variable_pattern.findall(ngrams_slice_one)) == 0:
            is_in_slice_two = True
        else:
            is_in_slice_two = False
        empty_text = False

    if len(ngrams_final_slice) != 0:
        if len(variable_pattern.findall(ngrams_final_slice)) > 0 and \
            len(variable_pattern.findall(ngrams_slice_one)) == 0 & \
            len(variable_pattern.findall(ngrams_slice_two)) == 0:
            is_in_final_slice = True
        else:
            is_in_final_slice = False
        empty_text = False

    if len(ngrams_slice_one) == 0 and len(ngrams_slice_two) == 0 and len(ngrams_final_slice) == 0:
        is_in_slice_one = False
        is_in_slice_two = False
        is_in_final_slice = False
        empty_text = True

    relevance_in_text_slices['slice_one'] = is_in_slice_one
    relevance_in_text_slices['slice_two'] = is_in_slice_two
    relevance_in_text_slices['final_slice'] = is_in_final_slice
    relevance_in_text_slices['empty_text'] = empty_text

    return relevance_in_text_slices


def search_in_words_list(words_frequency_slices, variable):
    """ Inspect variable position in frequency words list to determine protagonism

    Args:
        words_frequency_slices (dict)
        variable (str): Value to search

    Returns:
        [dict]: Formatted as: {'position': Bool}
    """

    more_relevant = False
    less_relevant = False
    medium_relevant = False
    empty_list = False
    relevance_in_words_list = {}

    slice_one = words_frequency_slices['slice_one']
    slice_two = words_frequency_slices['slice_two']
    final_slice = words_frequency_slices['final_slice']
    
    if variable == 'hospital sao luiz analia franco itaim jabaquara morumbi sao caetano':
        variable = 'hospital sao luiz'

    variable_pattern = re.compile(rf"\b{variable}\b")

    if len(slice_one) != 0:
        if len(variable_pattern.findall(slice_one)) > 0:
            more_relevant = True
        else:
            more_relevant = False

    if len(slice_two) != 0:
        if len(variable_pattern.findall(slice_two)) > 0 and \
                len(variable_pattern.findall(slice_one)) == 0:
            medium_relevant = True
        else:
            medium_relevant = False

    if len(final_slice) != 0:
        if len(variable_pattern.findall(final_slice)) > 0 and \
                len(variable_pattern.findall(slice_one)) == 0:
            less_relevant = True
        elif len(variable_pattern.findall(final_slice)) > 0 and \
                len(variable_pattern.findall(slice_two)) == 0:
            less_relevant = True
        else:
            less_relevant = False
        empty_list = False

    if len(slice_one) == 0 and len(slice_two) == 0 and len(final_slice) == 0:
        more_relevant = False
        less_relevant = False
        medium_relevant = False
        empty_list = True

    relevance_in_words_list['more_relevant'] = more_relevant
    relevance_in_words_list['medium_relevant'] = medium_relevant
    relevance_in_words_list['less_relevant'] = less_relevant
    relevance_in_words_list['empty_list'] = empty_list    
    return relevance_in_words_list
