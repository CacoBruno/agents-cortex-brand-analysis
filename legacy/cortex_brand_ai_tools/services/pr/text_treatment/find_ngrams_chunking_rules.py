from nltk.util import ngrams
from nltk import pos_tag, FreqDist, RegexpParser, Tree


rules = [
    "Bigram Rule: {<J.*|VB.*><NN|NNS>}",  # Adjectives or Verbs followed by Nouns
    "Bigram Rule: {<VB.*><J.*|VB.*>}",  # Verbs followed by Verbs or Adjectives
    "Bigram Rule: {<JJ.*|NN|NNS><JJ.*|NN|NNS>}",  # Adjectives/Nouns followed by Adajectives or Nouns
    "Bigram Rule: {<NN><NNS>}",  # Nouns and Nouns
    "Bigram Rule: {<NNP|NNPS><NNP|NNPS>}",
    "Trigram Rule: {<V.*|JJ.*|NN.*><DT|NN.*|V.*|IN.*><NN.*>}",
    "Quadrigram Rule: {<VB.*|NN.*><DT|V.*|NN.*><NN.*|DT><NN.*>}",
    "Quadrigram Rule: {<V.*|NN.*><JJ.*><RB.|NN.*><JJ>}",
    "Quadrigram Rule: {<RB.*|NN.*|JJ.*><JJ.*|NN.*|VB.*><NN.*|JJ.*|IN><NN.*|JJ.*>}",
    "Quadrigram Rule: {<JJ.*><NN.*|TO><TO|JJ.*><VB|NN>}",
    "Quadrigram Rule: {<NN.*><IN.*><JJ.*><NN.*>}",
    "Quadrigram Rule: {<MD|V.*><VB.*|RB.*><RB*><RB.*|VB.*>}",
    "Quadrigram Rule: {<NN.*|VB.*><NN.*|VB.*><DT|VB.*><RB.*|NN.*>}",
    "Quadrigram Rule: {<WDT><VB.*><TO><VB.*>}",
]


def n_grams_validator(df, column, gram):

    """Creates from a cleaned text the most relevant n-grams
    Args:
        df (Dataframe):  Dataframe
        column (String): Column with clean text
        gram (int): size of n_grams (acceptable: 2, 3 or 4)

    Returns:
        validated_ngrams (set): Set with the most relevant n_grams splitted by '_' (ie: oil_gas)
    """

    # ====================================
    # Rules definitions
    # J -> Any Adjective
    # VB -> Verb in base form
    # NN -> Any Nouns
    # DT -> Determiners (like stopwords)
    # RB -> Adverbs
    # ====================================

    bigram_rules = [
        "Bigram Rule: {<J.*|VB.*><NN|NNS>}",  # Adjectives or Verbs followed by Nouns
        "Bigram Rule: {<VB.*><J.*|VB.*>}",  # Verbs followed by Verbs or Adjectives
        "Bigram Rule: {<JJ.*|NN|NNS><JJ.*|NN|NNS>}",  # Adjectives/Nouns followed by Adajectives or Nouns
        "Bigram Rule: {<NN><NNS>}",  # Nouns and Nouns
        "Bigram Rule: {<NNP|NNPS><NNP|NNPS>}",
    ]

    trigram_rules = ["Trigram Rule: {<V.*|JJ.*|NN.*><DT|NN.*|V.*|IN.*><NN.*>}"]

    quadrigram_rules = [
        "Quadrigram Rule: {<VB.*|NN.*><DT|V.*|NN.*><NN.*|DT><NN.*>}",
        "Quadrigram Rule: {<V.*|NN.*><JJ.*><RB.|NN.*><JJ>}",
        "Quadrigram Rule: {<RB.*|NN.*|JJ.*><JJ.*|NN.*|VB.*><NN.*|JJ.*|IN><NN.*|JJ.*>}",
        "Quadrigram Rule: {<JJ.*><NN.*|TO><TO|JJ.*><VB|NN>}",
        "Quadrigram Rule: {<NN.*><IN.*><JJ.*><NN.*>}",
        "Quadrigram Rule: {<MD|V.*><VB.*|RB.*><RB*><RB.*|VB.*>}",
        "Quadrigram Rule: {<NN.*|VB.*><NN.*|VB.*><DT|VB.*><RB.*|NN.*>}",
        "Quadrigram Rule: {<WDT><VB.*><TO><VB.*>}",
    ]

    validated_ngrams = {}
    most_common_grams = set()

    if gram == 2:
        rules = bigram_rules
    elif gram == 3:
        rules = trigram_rules
    else:
        rules = quadrigram_rules

    # ================================================
    # Word Tagging
    # =================================================
    for sentence in df[column]:
        words = sentence.split()
        tags = pos_tag(words)
        word_grams = ngrams(tags, gram)
        most_common = FreqDist(word_grams)
        [
            most_common_grams.add(pair)
            for (pair, count) in most_common.items()
            if count > 3
        ]

    # ================================================
    # Analyze tagged words based on n-gram rules
    # =================================================
    for rule in rules:
        parser = RegexpParser(rule)
        for value in most_common_grams:
            tree = parser.parse(value)
            for leaf in tree:
                if isinstance(leaf, Tree):
                    join_words = [node[0] for node in leaf]
                    validated_ngrams[str(" ".join(join_words))] = "_".join(
                        join_words
                    ).replace("__", "_")

    return validated_ngrams
