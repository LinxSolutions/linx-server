import nltk
import string


class Curriculum:

    def __init__(self, language, parts):
        self.language = language
        self.parts = parts

    def generate(self, captions):
        if 1 in self.parts:
            nouns = []
            adj = []
            verb = []
            stop = nltk.corpus.stopwords.words('english') + list(string.punctuation)
            is_noun = lambda pos: pos[:2] == 'NN'
            is_adj = lambda pos: pos[:2] == 'JJ'
            is_verb = lambda pos: pos[:2] == 'VB'
            for caption in captions:
                filtered_words = [i for i in nltk.word_tokenize(caption.lower()) if i not in stop]
                nouns.append([word for (word, pos) in nltk.pos_tag(filtered_words) if is_noun(pos)])
                adj.append([word for (word, pos) in nltk.pos_tag(filtered_words) if is_adj(pos)])
                verb.append([word for (word, pos) in nltk.pos_tag(filtered_words) if is_verb(pos)])
        if 2 in self.parts:
            pass