""" Implements the cortex methodology for protagonism classification """

#### Setup ####
import math
from nltk import sent_tokenize

def slicing(text):
    """Divides the text into slices according to the predefined sizes

    Args:
        text (str): News body
    Returns:
        [dict]: Containing: indication of the slice as key and the division of the text as value
    """
    slices = {}

    sent_text = sent_tokenize(text)
    text_size = len(sent_text)
    first_third = math.ceil(text_size * 0.15)
    second_third = math.ceil((text_size * 0.80))

    if first_third == 0 and second_third == 0:
        first_third_text = " ".join(sent_text)
        second_third_text = ''
        final_part_text = ''
    elif first_third != 0 and second_third == 0:
        first_third_text = " ".join(sent_text)
        second_third_text = ''
        final_part_text = ''
    else:
        first_third_text = " ".join(sent_text[0:first_third])
        second_third_text = " ".join(sent_text[first_third:second_third])
        final_part_text = " ".join(sent_text[second_third:])

    slices['slice_one'] = first_third_text
    slices['slice_two'] = second_third_text
    slices['final_slice'] = final_part_text

    return slices