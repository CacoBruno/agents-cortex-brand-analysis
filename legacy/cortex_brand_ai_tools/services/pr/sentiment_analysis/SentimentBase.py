""" Accesses and formats the word and term databases for sentiment analysis """

#### Setup ####
import os
import codecs
from inspect import getsourcefile
import ast


class SentimentBase:
    """ Accesses and formats the word and term databases for sentiment analysis """

    def __init__(self, words_file="pt_words.py", expressions_file="pt_expressions.py"):
        """ Initialize the Words and Expressions Base.

        Args:
            words_file (str, optional): Path to words base. Defaults to "pt_words.txt".
            expressions_file (str, optional): Path to expression base. Defaults
            to "pt_expressions.txt".
        """
        _this_module_file_path_ = os.path.abspath(getsourcefile(lambda: 0))

        words_full_filepath = os.path.join(
            os.path.dirname(_this_module_file_path_), words_file)
        expressions_full_filepath = os.path.join(
            os.path.dirname(_this_module_file_path_), expressions_file)

        with codecs.open(words_full_filepath, encoding='utf-8') as file:
            self.words_full_filepath = file.read()

        with codecs.open(expressions_full_filepath, encoding='utf-8') as file:
            self.expression_full_filepath = file.read()

    def get_words_dictionary(self):
        """Converts words file to a dictionary (keys as words and values as weights)

        Returns:
            [dict]
        """

        words_dictionary = {}

        for line in self.words_full_filepath.rstrip('\n').split('\n'):
            if not line:
                continue
            line = ast.literal_eval(line)
            word = line[0]
            measure = line[1]
            words_dictionary[word] = float(measure)

        return words_dictionary

    def get_expressions_dictionary(self):
        """ Converts expressions file to a dictionary (keys as expressions and values as weights)

        Returns:
           [dict]
        """

        expressions_dictionary = {}

        for line in self.expression_full_filepath.rstrip('\n').split('\n'):
            if not line:
                continue
            line = ast.literal_eval(line)
            word = line[0]
            measure = line[1]
            expressions_dictionary[word] = float(measure)

        return expressions_dictionary
