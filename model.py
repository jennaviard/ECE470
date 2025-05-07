import uuid
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from threading import Lock
import random

class WAVEREQ(Enum):
    CRE8 = 200
    JOIN = 201
    GLST = 202
    STRT = 203
    CARD = 204
    CLUE = 205
    GUESS = 206
    SCRB = 208
    ENDG = 210
    CHAT = 211

@dataclass
class Player:
    username: str
    team: str
    is_psychic: bool = False

@dataclass
class Card:
    topic: str
    left_hint: str
    right_hint: str
    target_start: int
    target_end: int

    def center(self):
        return (self.target_start + self.target_end) // 2

@dataclass
class Game:
    game_name: str
    pin: str
    creator: str
    game_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    players: List[Player] = field(default_factory=list)
    state: str = "LOBBY"
    cards: List[Card] = field(default_factory=list)
    current_card: Optional[Card] = None
    clue: Optional[str] = None
    scores: Dict[str, int] = field(default_factory=lambda: {"TeamA": 0, "TeamB": 0})
    guesses: Dict[str, int] = field(default_factory=dict)
    chat_log: List[str] = field(default_factory=list)
    round_number: int = 0
    psychic_index: int = -1
    current_team: str = "TeamA"

    def add_player(self, username: str, team: str):
        if self.state != "LOBBY":
            raise Exception("Cannot join; game already started.")
        self.players.append(Player(username=username, team=team))

    def start_game(self):
        if self.state != "LOBBY":
            raise Exception("Game already started or ended.")
        self.state = "IN_PROGRESS"
        self.current_team = "TeamA"

    def assign_psychic(self):
        for p in self.players:
            p.is_psychic = False
        if not self.players:
            return None
        eligible = [p for p in self.players if p.team == self.current_team]
        self.psychic_index = self.players.index(eligible[self.round_number % len(eligible)])
        self.players[self.psychic_index].is_psychic = True
        return self.players[self.psychic_index].username

    def submit_clue(self, clue: str, psychic: str):
        self.clue = clue

    def submit_guess(self, team: str, value: int):
        if not (1 <= value <= 20):
            raise ValueError("Guess must be an integer between 1 and 20.")
        self.guesses[team] = value

    def evaluate_guess(self):
        psychic = self.players[self.psychic_index]
        main_team = psychic.team
        guess = self.guesses.get(main_team)
        if guess is None or self.current_card is None:
            return None

        start = self.current_card.target_start
        end = self.current_card.target_end
        center = self.current_card.center()

        if start <= end:
            in_arc = start <= guess <= end
        else:
            in_arc = guess >= start or guess <= end

        if guess == center:
            points = 4
        elif in_arc:
            points = 3
        elif abs(guess - center) % 20 == 1:
            points = 2
        elif abs(guess - center) % 20 == 2:
            points = 1
        else:
            points = 0

        self.scores[main_team] += points

        return {
            "team_guess": guess,
            "target_range": f"{start} - {end}",
            "target_center": center,
            "points": points,
            "TeamA": self.scores["TeamA"],
            "TeamB": self.scores["TeamB"]
        }

    def next_round(self):
        self.round_number += 1
        self.clue = None
        self.current_card = None
        self.guesses.clear()
        self.current_team = "TeamB" if self.current_team == "TeamA" else "TeamA"
        for p in self.players:
            p.is_psychic = False

    def draw_card(self) -> Optional[Card]:
        if not self.cards:
            self.generate_default_cards()
        if not self.cards:
            return None
        card = self.cards.pop(0)
        self.current_card = card
        return card

    def generate_default_cards(self):
        card_data = [
            ("Hot", "Cold"), ("Safe for Work", "Not Safe for Work"), ("Genius", "Stupid"),
            ("Overrated", "Underrated"), ("Moral", "Immoral"), ("Sweet", "Savory"),
            ("Introvert", "Extrovert"), ("Realistic", "Fantastical"), ("Mainstream", "Obscure"),
            ("Casual", "Formal"), ("Cheap", "Expensive"), ("Useful", "Useless"),
            ("Healthy", "Unhealthy"), ("Modern", "Old-fashioned"), ("Funny", "Serious"),
            ("Popular", "Unpopular"), ("Love", "Hate"), ("Hard", "Easy"), ("Necessary", "Unnecessary"),
            ("Cool", "Uncool"), ("Brave", "Cowardly"), ("Messy", "Organized"), ("Cliché", "Original"),
            ("Common", "Rare"), ("Quiet", "Loud"), ("Bright", "Dark"), ("Good for you", "Bad for you"),
            ("Overprepared", "Underprepared"), ("Reliable", "Unreliable"), ("Predictable", "Surprising"),
            ("Big Risk", "No Risk"), ("Fast", "Slow"), ("Public", "Private"), ("Generous", "Greedy"),
            ("Fiction", "Nonfiction"), ("Simple", "Complicated"), ("Strong", "Weak"), ("Free", "Costly"),
            ("Honest", "Deceptive"), ("Useful Skill", "Useless Skill"), ("Too Much", "Not Enough"),
            ("Peaceful", "Chaotic"), ("Fun", "Boring"), ("Soft", "Hard"), ("Natural", "Artificial"),
            ("Friendly", "Hostile"), ("Optimistic", "Pessimistic"), ("Efficient", "Wasteful"),
            ("Energetic", "Tired"), ("Dangerous", "Safe"), ("Spicy", "Bland"), ("Big", "Small"),
            ("Tall", "Wide"), ("Short", "Thin"), ("New", "Ancient"), ("Lame", "Exciting"),
            ("Sweet", "Bitter"), ("Sour", "Tart"), ("Cool", "Hot"), ("Loud", "Silent"),
            ("Shy", "Bold"), ("Fancy", "Simple"), ("Plain", "Luxury"), ("Cozy", "Uncomfortable"),
            ("Icy", "Hot"), ("Grim", "Bright"), ("Happy", "Cheerful"), ("Sad", "Depressing"),
            ("Dry", "Wet"), ("Weird", "Normal"), ("Basic", "Complex"), ("Creative", "Unimaginative"),
            ("Grounded", "Flighty"), ("Polished", "Rough"), ("Clean", "Dirty"), ("Delicate", "Rugged"),
            ("Orderly", "Chaotic"), ("Open-minded", "Close-minded"), ("Passive", "Aggressive"),
            ("Playful", "Serious"), ("Logical", "Emotional"), ("Literal", "Figurative"),
            ("Tidy", "Messy"), ("Overt", "Subtle"), ("Routine", "Spontaneous"), ("Hyped", "Chill"),
            ("Innovative", "Traditional"), ("Digital", "Analog"), ("Organic", "Synthetic"),
            ("Main Character", "Side Character"), ("Awkward", "Charming"), ("Extinct", "Thriving"),
            ("Groundbreaking", "Typical"), ("High Effort", "Low Effort"), ("Popular", "Underground"),
            ("Smart", "Ignorant"), ("Seasoned", "Inexperienced"), ("Overkill", "Underwhelming"),
            ("Wild", "Tame"), ("Hopeful", "Hopeless"), ("Impressive", "Forgettable"),
            ("Open", "Closed"), ("Massive", "Tiny"), ("Overconfident", "Insecure"),
            ("Overdressed", "Underdressed"), ("Powerful", "Powerless"), ("Grounded", "Unrealistic"),
            ("Bright", "Muted"), ("Talkative", "Quiet"), ("Controversial", "Uncontroversial"),
            ("Nostalgic", "Futuristic"), ("Altruistic", "Selfish"), ("Cringe", "Cool"),
            ("Rebellious", "Obedient"), ("Edgy", "Wholesome"), ("Dramatic", "Calm"),
            ("Silly", "Serious"), ("Heavy", "Light"), ("Warm", "Cool"), ("Sharp", "Dull"),
            ("Private", "Public"), ("Obvious", "Ambiguous"), ("Literal", "Metaphorical"),
            ("Edible", "Inedible"), ("Human-made", "Natural"), ("Expected", "Unexpected"),
            ("Traditional", "Modern"), ("Local", "Global"), ("Impersonal", "Personal"),
            ("Forgiving", "Grudging"), ("Rigid", "Flexible"), ("Noisy", "Quiet"),
            ("Urban", "Rural"), ("Safe", "Risky"), ("Imaginative", "Literal"),
            ("Extravagant", "Minimal"), ("Crowded", "Empty"), ("Exclusive", "Inclusive"),
            ("Active", "Passive"), ("Fancy", "Plain"), ("Slick", "Clunky"), ("Dense", "Sparse"),
            ("Expressive", "Reserved"), ("Familiar", "Unfamiliar"), ("Approachable", "Intimidating"),
            ("Bright", "Dim"), ("Physical", "Digital"), ("Popular", "Niche")
        ]
        random.shuffle(card_data)
        self.cards = [Card(f"{l} vs {r}", l, r, random.randint(1, 15), random.randint(16, 20)) for l, r in card_data]


    def check_winner(self, point_threshold: int = 10) -> Optional[str]:
        for team, score in self.scores.items():
            if score >= point_threshold:
                return team
        return None

class GameManager:
    def __init__(self):
        self.games: Dict[str, Game] = {}
        self.lock = Lock()

    def create_game(self, game_name: str, pin: str, username: str) -> Optional[Game]:
        with self.lock:
            for g in self.games.values():
                if g.game_name == game_name:
                    return None

            new_game = Game(game_name=game_name, pin=pin, creator=username)
            new_game.add_player(username, team="TeamA")
            new_game.generate_default_cards()
            self.games[new_game.game_id] = new_game
            return new_game

    def join_game(self, game_name: str, pin: str, username: str) -> Optional[Game]:
        with self.lock:
            for game in self.games.values():
                if game.game_name == game_name and game.pin == pin:
                    if any(p.username == username for p in game.players):
                        return None
                    team = "TeamB" if sum(p.team == "TeamB" for p in game.players) <= sum(p.team == "TeamA" for p in game.players) else "TeamA"
                    game.add_player(username, team)
                    return game
            return None

    def get_game_by_id(self, game_id: str) -> Optional[Game]:
        with self.lock:
            return self.games.get(game_id)

    def list_games(self) -> List[str]:
        with self.lock:
            return [game.game_name for game in self.games.values() if game.state == "LOBBY"]

    def end_game(self, game_id: str) -> bool:
        with self.lock:
            if game_id in self.games:
                self.games[game_id].state = "ENDED"
                return True
            return False
