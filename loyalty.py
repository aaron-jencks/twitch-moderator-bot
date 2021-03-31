import spacy


sign_on_bonus = 300
nlp = spacy.load("en_core_web_sm")


def assign_message_score(msg: str) -> int:
    doc = nlp(msg)
    pos = set()
    lemmas = set()
    for token in doc:
        pos.add(token.pos_)
        lemmas.add(token.lemma_)
    pos_score = len(pos) / 8
    lemma_score = pos_score * len(lemmas)
    score = int(lemma_score) + 1
    return score


def determine_visit_bonus(streak: int) -> int:
    return streak * 50 + 100


class LoyaltyRedeem:
    def __init__(self, title: str, description: str, cost: int):
        self.title = title
        self.description = description
        self.cost = cost

    def __lt__(self, other):
        if isinstance(other, LoyaltyRedeem.__class__):
            return self.cost < other.cost
        return False

    def __eq__(self, other):
        if isinstance(other, LoyaltyRedeem.__class__):
            return self.cost == other.cost
        return False
