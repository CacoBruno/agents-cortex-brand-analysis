""" Implements cortex mothodology for sentimento classification """

#### Setup ####
import math
from services.pr.sentiment_analysis import SentimentBase as Words


class CortexLexicon():
    """ Implements Cortex Methodology for sentimento classification """

    def __init__(self, extra_terms):

        # Words Object
        words = Words.SentimentBase()
        self.words = words.get_words_dictionary()
        self.expressions = words.get_expressions_dictionary()

        # Extra terms as parameters
        self.extra_terms = extra_terms
        
    def adjust_scores(self, sentiments):
        """ Given a weight dictionary, this function distinguishes
            between positive and negative values.

        Args:
            sentiments (Dictionary): Dictionary of words and its weights assined

        Returns:
            [Float]: Returns two floats corresponding to positive and negative scores
        """

        pos_sum = 0.0
        neg_sum = 0.0

        for sentiment_score in sentiments:

            if sentiment_score > 0:
                pos_sum += (float(sentiment_score) + 1)
            if sentiment_score < 0:
                neg_sum += (float(sentiment_score) - 1)

        return pos_sum, neg_sum
    
    def define_sentiment_scores(self, pos_sum, neg_sum):
        """ This function is responsible for receiving positive and negative scores
            and updating them with the penalty value. After processing, this function
            returns the final probabilities for positive and negative level in sentences.

        Args:
            pos_sum (float)
            neg_sum (float)
            penalize (float)

        Returns:
            [list]: List of floats (probabilities of positive and negative)
        """

        if pos_sum > math.fabs(neg_sum):
            pos_sum += 0.1
        elif pos_sum < math.fabs(neg_sum):
            neg_sum -= 0.1

        # Calculates probability for each label
        total = pos_sum + math.fabs(neg_sum)
        if total > 0:
            pos_sum = math.fabs(pos_sum / total)
            neg_sum = math.fabs(neg_sum / total)

        return neg_sum, pos_sum

    def get_dictionaries(self):
        """ Turns list of words/expressions into dictionaries

        Returns:
            [dict]
        """

        # Terms from object updated with terms received from parameters
        extra_terms = self.extra_terms
        if len(extra_terms) > 0:
            for key, value in extra_terms.items():
                if len(key.split(' ')) > 1:
                    self.expressions[key] = value
                else:
                    self.words[key] = value

        words_dictionary = self.words
        expressions_dictionary = self.expressions

        return words_dictionary, expressions_dictionary

    def __call__(self, sentence, to_show=False):
        """ Receives a sentence and search each terms in the Word and Expression base.
            Finding the terms in the bases, it assigns the corresponding weight,
            therefore, it receives a weight of 0.
            
        Args: 
            sentence (str):  Clean sentence
            to_show (bool): Show sentiment weights. Default: False

        Returns:
            [list]: List of floats (probabilities of positive and negative)
        """

        words_dictionary, expressions_dictionary = self.get_dictionaries()

        sentiments = {}
        for item in sentence.split():
            item_lowercase = item.lower()
            if item_lowercase in words_dictionary.keys():

                sentiments[item_lowercase] = words_dictionary[item_lowercase]
            else:
                sentiments[item_lowercase] = 0

        if to_show:
            print(sentiments)

        penalize_neg = 0
        penalize_pos = 0

        for expression in expressions_dictionary:
            if expression in sentence:
                if expressions_dictionary[expression] < 0:
                    penalize_neg += math.fabs(expressions_dictionary[expression])
                    if to_show:
                        print(expression, expressions_dictionary[expression])
                else:
                    penalize_pos += expressions_dictionary[expression]
                    if to_show:
                        print(expression, expressions_dictionary[expression])                

        penalize_neg = penalize_neg * -1

        # Adjusts scores for positive and negative
        pos_sum, neg_sum = self.adjust_scores(sentiments.values())
        pos_sum += penalize_pos
        neg_sum += penalize_neg
        
        # Define sentiment scores probabilities
        return self.define_sentiment_scores(pos_sum, neg_sum)
