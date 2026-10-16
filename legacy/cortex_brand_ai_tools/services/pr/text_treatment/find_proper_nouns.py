import re
from collections import Counter, defaultdict

import nltk


def find_proper_nouns_and_retag_sentences(doc_val):
    tagged_sents_tokens = doc_val["tagged_tokens"].copy()
    proper_nouns_by_sentence = defaultdict(list)
    N = 9
    for n in range(N, 0, -1):

        # Get list of tagged Ngrams
        ngrams_ref = {}
        for k, tagged_sent_tokens in tagged_sents_tokens.items():
            if len(tagged_sent_tokens) >= n:
                ngrams_ref[k] = [grams for grams in nltk.ngrams(tagged_sent_tokens, n)]

        # Find Proper Nouns among Ngrams
        current_pn = defaultdict(list)
        discard_tags = set(["."] + ["PNOUN" + str(i) for i in range(N, 0, -1)])
        for k, ngrams in ngrams_ref.items():
            for idx, ngram in enumerate(ngrams):
                tags = [tagged_word[1] for tagged_word in ngram]
                if (
                    len(set(tags).intersection(discard_tags)) == 0
                    and len(ngram[0][0]) > 1
                    and ngram[0][0][0].isupper()
                    and (ngram[-1][0][0].isupper() or ngram[-1][0][0].isdigit())
                ):
                    word_lst = [
                        tagged_word[0]
                        for tagged_word in ngram
                        if tagged_word[1] not in ["ADP"]
                    ]
                    s_check = "".join(word[0] for word in word_lst)
                    pat = re.compile(r"[^a-zA-Z ]+")
                    if re.sub(pat, "", s_check).isupper():
                        proper_noun = " ".join(
                            [tagged_word[0] for tagged_word in ngram]
                        )
                        current_pn[k].append(proper_noun)
                        proper_nouns_by_sentence[k].append(proper_noun)

                        # Retagged word
                        for i in range(idx, idx + n):
                            tagged_sents_tokens[k][i] = (
                                tagged_sents_tokens[k][i][0],
                                "PNOUN" + str(n),
                            )

    return proper_nouns_by_sentence, tagged_sents_tokens


def count_proper_nouns(proper_nouns_by_sentence):
    return Counter([pn for tpl, lst in proper_nouns_by_sentence.items() for pn in lst])
