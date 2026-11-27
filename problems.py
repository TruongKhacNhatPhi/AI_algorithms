import random

DELTA = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}
OPPOSITE = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}


class VacuumProblem:
    id = "vacuum"
    name = "Vacuum Cleaner"
    default_start = ("A", "Dirty", "Dirty")

    @staticmethod
    def is_goal(s):
        return s[1] == "Clean" and s[2] == "Clean"

    @staticmethod
    def actions(s):
        return ["Suck", "Left", "Right"]

    @staticmethod
    def result(s, a):
        pos, room_a, room_b = s
        if a == "Left":
            return ("A", room_a, room_b)
        if a == "Right":
            return ("B", room_a, room_b)
        if pos == "A":
            return (pos, "Clean", room_b)
        return (pos, room_a, "Clean")

    @staticmethod
    def step_cost(s, a, ns):
        return 1

    @staticmethod
    def format_start(s):
        return f"Initial state: Robot in Room {s[0]}, Room A: {s[1]}, Room B: {s[2]}"

    @staticmethod
    def format_step(a, i, is_goal):
        suffix = " -> Goal Reached!" if is_goal else ""
        return f"Step {i}: Action [{a}]{suffix}"


class Puzzle8Problem:
    id = "puzzle8"
    name = "8-Puzzle"
    default_start = (1, 2, 3, 4, 0, 6, 7, 5, 8)
    goal = (1, 2, 3, 4, 5, 6, 7, 8, 0)

    @classmethod
    def is_goal(cls, s):
        return s == cls.goal

    @staticmethod
    def actions(s):
        b = s.index(0)
        r, c = divmod(b, 3)
        moves = []
        if r > 0:
            moves.append("Up")
        if r < 2:
            moves.append("Down")
        if c > 0:
            moves.append("Left")
        if c < 2:
            moves.append("Right")
        return moves

    @staticmethod
    def result(s, a):
        b = s.index(0)
        r, c = divmod(b, 3)
        dr, dc = DELTA[a]
        t = (r + dr) * 3 + (c + dc)
        nxt = list(s)
        nxt[b], nxt[t] = nxt[t], 0
        return tuple(nxt)

    @staticmethod
    def step_cost(s, a, ns):
        return 1

    @staticmethod
    def inversions(s):
        arr = [x for x in s if x != 0]
        return sum(1 for i in range(len(arr)) for j in range(i + 1, len(arr)) if arr[i] > arr[j])

    @classmethod
    def is_solvable(cls, s):
        return cls.inversions(s) % 2 == 0

    @classmethod
    def shuffled(cls, moves=20):
        s = cls.goal
        last = None
        for _ in range(moves):
            opts = [a for a in cls.actions(s) if a != OPPOSITE.get(last)]
            a = random.choice(opts)
            s = cls.result(s, a)
            last = a
        return s

    @staticmethod
    def format_start(s):
        return "Initial configuration"

    @staticmethod
    def format_step(a, i, is_goal):
        suffix = " -> Goal Reached!" if is_goal else ""
        return f"Step {i}: Slide [{a}]{suffix}"


GRAPH_PRESETS = {
    "classic": {
        "name": "Classic Trap",
        "start": "S",
        "goal": "G",
        "pos": {
            "S": (0.10, 0.50),
            "A": (0.48, 0.18),
            "B": (0.28, 0.78),
            "C": (0.50, 0.78),
            "D": (0.72, 0.78),
            "E": (0.68, 0.45),
            "G": (0.90, 0.48),
        },
        "edges": [
            ("S", "A", 10),
            ("A", "G", 10),
            ("S", "B", 2),
            ("B", "C", 3),
            ("C", "D", 2),
            ("D", "G", 3),
            ("A", "C", 6),
            ("B", "E", 8),
            ("E", "G", 7),
        ],
    },
    "romania": {
        "name": "Romania Map",
        "start": "Arad",
        "goal": "Bucharest",
        "pos": {
            "Arad": (0.10, 0.36),
            "Zerind": (0.14, 0.15),
            "Oradea": (0.28, 0.14),
            "Timisoara": (0.12, 0.68),
            "Lugoj": (0.28, 0.80),
            "Sibiu": (0.36, 0.38),
            "Fagaras": (0.62, 0.22),
            "Rimnicu": (0.48, 0.62),
            "Pitesti": (0.68, 0.66),
            "Bucharest": (0.88, 0.50),
        },
        "edges": [
            ("Arad", "Zerind", 75),
            ("Zerind", "Oradea", 71),
            ("Oradea", "Sibiu", 151),
            ("Arad", "Sibiu", 140),
            ("Arad", "Timisoara", 118),
            ("Timisoara", "Lugoj", 111),
            ("Sibiu", "Fagaras", 99),
            ("Fagaras", "Bucharest", 211),
            ("Sibiu", "Rimnicu", 80),
            ("Rimnicu", "Pitesti", 97),
            ("Pitesti", "Bucharest", 101),
        ],
    },
}


class WeightedGraphProblem:
    id = "graph"
    name = "Weighted Graph"
    default_start = "S"
    active_preset = "classic"

    @classmethod
    def set_preset(cls, key):
        cls.active_preset = key
        cls.default_start = GRAPH_PRESETS[key]["start"]

    @classmethod
    def preset(cls):
        return GRAPH_PRESETS[cls.active_preset]

    @classmethod
    def is_goal(cls, s):
        return s == cls.preset()["goal"]

    @classmethod
    def _adj(cls):
        adj = {node: [] for node in cls.preset()["pos"]}
        for u, v, w in cls.preset()["edges"]:
            adj[u].append((v, w))
            adj[v].append((u, w))
        return adj

    @classmethod
    def actions(cls, s):
        return [nbr for nbr, _ in cls._adj().get(s, [])]

    @classmethod
    def result(cls, s, a):
        return a

    @classmethod
    def step_cost(cls, s, a, ns):
        for nbr, w in cls._adj().get(s, []):
            if nbr == ns:
                return w
        return 1

    @classmethod
    def format_start(cls, s):
        return f"Start at [{s}] -> Target [{cls.preset()['goal']}]"

    @classmethod
    def format_step(cls, a, i, is_goal):
        suffix = " -> Goal Reached!" if is_goal else ""
        return f"Step {i}: Move to [{a}]{suffix}"


PROBLEMS = {
    "vacuum": VacuumProblem,
    "puzzle8": Puzzle8Problem,
    "graph": WeightedGraphProblem,
}
