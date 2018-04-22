import nltk

class Analyzer():
    """Implements sentiment analysis."""
    def __init__(self, positives, negatives):
        """Initialize Analyzer."""
        self.positives = []
        self.negatives = []

        with open(positives, "r") as f_positive:
            for line in f_positive:
                if line.startswith(';'):
                    next(f_positive)
                else:
                    self.positives.append(line)

        with open(negatives, "r") as f_negative:
            for line in f_negative:
                if line.startswith(';'):
                    next(f_negative)
                else:
                    self.negatives.append(line)

        for n in range(len(self.positives)):
            self.positives[n] = self.positives[n].strip('\n')
        for n in range(len(self.negatives)):
            self.negatives[n] = self.negatives[n].strip('\n')


    def analyze(self, text):
        """Analyze text for sentiment, returning its score."""
        tokens = nltk.tokenize.casual.casual_tokenize(text)

        score = 0
        for element in tokens:
            if element in self.positives:
                score += 1
            elif element in self.negatives:
                score += -1
            else:
                score += 0
        return score
