import ctypes
import math

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import pygame

from bfs import BFS
from dfs import DFS
from problems import GRAPH_PRESETS, PROBLEMS, Puzzle8Problem, VacuumProblem, WeightedGraphProblem
from ucs import UCS

# ============================================================
# 1. Theme & Color Palette (Warm Paper & Sage)
# ============================================================
W, H = 1280, 868
FPS = 60

BG_PAGE = (237, 232, 223)
CARD_BG = (250, 248, 244)
SURFACE_SOFT = (241, 237, 228)
SURFACE_ARENA = (230, 224, 212)
BORDER = (220, 213, 201)
BORDER_DARK = (197, 189, 176)

TEXT_MAIN = (36, 34, 31)
TEXT_MUTED = (107, 101, 92)

PRIMARY = (67, 56, 202)
PRIMARY_SOFT = (232, 230, 248)

DFS_ACCENT = (194, 65, 12)
DFS_SOFT = (250, 232, 223)

UCS_ACCENT = (15, 118, 110)
UCS_SOFT = (222, 245, 242)

CLEAN_BG = (230, 242, 234)
CLEAN_BORDER = (159, 209, 175)
CLEAN_TEXT = (28, 94, 55)

DIRTY_BG = (248, 234, 216)
DIRTY_BORDER = (229, 184, 135)
DIRTY_TEXT = (154, 52, 18)

TILE_BG = (255, 253, 249)
TILE_LIP = (207, 199, 184)
TILE_LOCKED_BG = (223, 240, 228)
TILE_LOCKED_LIP = (149, 201, 166)
TILE_MOVED_BG = (236, 234, 250)
TILE_MOVED_BORDER = (129, 140, 248)


# ============================================================
# 2. Modular Search Algorithms Registry
# ============================================================
ALGORITHMS = {
    "BFS": {
        "id": "BFS",
        "name": "Breadth-First Search",
        "short": "BFS",
        "category": "Uninformed",
        "structure": "Queue (FIFO)",
        "badge": "BFS · Optimal Step Count",
        "accent": PRIMARY,
        "soft": PRIMARY_SOFT,
        "run": BFS,
    },
    "DFS": {
        "id": "DFS",
        "name": "Depth-First Search",
        "short": "DFS",
        "category": "Uninformed",
        "structure": "Stack (LIFO)",
        "badge": "DFS · Depth-First Traversal",
        "accent": DFS_ACCENT,
        "soft": DFS_SOFT,
        "run": DFS,
    },
    "UCS": {
        "id": "UCS",
        "name": "Uniform Cost Search",
        "short": "UCS",
        "category": "Uninformed",
        "structure": "Priority Queue",
        "badge": "UCS · Lowest Path Cost",
        "accent": UCS_ACCENT,
        "soft": UCS_SOFT,
        "run": UCS,
    },
}


def compute_path_cost(problem, res):
    if not res or not res["found"]:
        return None
    if res.get("cost") is not None:
        return res["cost"]
    path, actions = res["path"], res["actions"]
    cost_fn = getattr(problem, "step_cost", lambda s, a, ns: 1)
    return sum(cost_fn(path[i], actions[i], path[i + 1]) for i in range(len(actions)))


# ============================================================
# 3. UI Drawing Helpers
# ============================================================
def draw_rounded_rect(surf, rect, color, radius=12, border_color=None, border_width=1):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border_color is not None and border_width > 0:
        pygame.draw.rect(surf, border_color, rect, width=border_width, border_radius=radius)


def draw_button(surf, rect, text, font, bg, fg, border=None, hover=False, radius=8):
    col = tuple(max(0, min(255, c - 10)) for c in bg) if hover else bg
    draw_rounded_rect(surf, rect, col, radius=radius, border_color=border, border_width=1 if border else 0)
    lbl = font.render(text, True, fg)
    surf.blit(lbl, lbl.get_rect(center=rect.center))


# ============================================================
# 4. Main Visualizer Application
# ============================================================
class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("AI Search Algorithms — Visualizer")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()

        self.f_title = pygame.font.SysFont("Segoe UI", 21, bold=True)
        self.f_sub = pygame.font.SysFont("Segoe UI", 13)
        self.f_h2 = pygame.font.SysFont("Segoe UI", 15, bold=True)
        self.f_btn = pygame.font.SysFont("Segoe UI", 13, bold=True)
        self.f_body = pygame.font.SysFont("Segoe UI", 13)
        self.f_small = pygame.font.SysFont("Segoe UI", 11, bold=True)
        self.f_tile = pygame.font.SysFont("Segoe UI", 28, bold=True)
        self.f_metric = pygame.font.SysFont("Segoe UI", 16, bold=True)

        self.problem_id = "graph"
        self.algo_id = "UCS"
        self.starts = {
            "vacuum": VacuumProblem.default_start,
            "puzzle8": Puzzle8Problem.default_start,
            "graph": WeightedGraphProblem.default_start,
        }
        self.mode = "solution"
        self.result = None
        self.frames = []
        self.idx = 0
        self.playing = False
        self.speed_ms = 420
        self.play_accum = 0.0
        self.compare_rows = []
        self.dragging_scrub = False

        self.drone_x = 0.0
        self.vortex_angle = 0.0
        self.dust_phase = 0.0
        self.tile_pos = {}
        self.graph_cursor = [0.1, 0.5]
        self.init_anim_positions()

        self.buttons = []
        self.scrub_rect = pygame.Rect(0, 0, 1, 1)
        self.compare_rects = []

        self.run_search(auto_play=False)

    def cur_problem(self):
        return PROBLEMS[self.problem_id]

    def cur_algo(self):
        return ALGORITHMS[self.algo_id]

    def cur_start(self):
        return self.starts[self.problem_id]

    def init_anim_positions(self):
        self.drone_x = 265.0 if self.starts["vacuum"][0] == "A" else 635.0
        for i, v in enumerate(self.starts["puzzle8"]):
            if v != 0:
                r, c = divmod(i, 3)
                self.tile_pos[v] = [float(c), float(r)]
        preset = WeightedGraphProblem.preset()
        st = self.starts["graph"]
        if st in preset["pos"]:
            self.graph_cursor = list(preset["pos"][st])

    def build_frames(self):
        r = self.result
        p = self.cur_problem()
        if not r:
            return []

        if self.mode == "search":
            ds = self.cur_algo()["structure"]
            frames = []
            for k, t in enumerate(r["trace"]):
                cost_part = f" · Cost: {t['cost']}" if "cost" in t else ""
                frames.append({
                    "state": t["state"],
                    "action": t["action"],
                    "hl": -1,
                    "cost": t.get("cost"),
                    "label": f"Expanding #{k + 1} ({t['state'] if self.problem_id == 'graph' else 'Depth ' + str(t['depth'])}) · {ds}: {t['frontier_size']}{cost_part}",
                })
            if r["found"] and self.problem_id != "graph":
                frames.append({
                    "state": r["path"][-1],
                    "action": r["actions"][-1] if r["actions"] else None,
                    "hl": -1,
                    "label": f"Goal Reached in {len(r['path']) - 1} steps.",
                })
            elif not r["found"]:
                last_s = r["trace"][-1]["state"] if r["trace"] else self.cur_start()
                frames.append({
                    "state": last_s,
                    "action": None,
                    "hl": -1,
                    "label": "Stopped: Limit reached." if r["aborted"] else "No solution exists.",
                })
            return frames

        frames = []
        cum_cost = 0
        cost_fn = getattr(p, "step_cost", lambda s, a, ns: 1)
        for i, s in enumerate(r["path"]):
            hl = r["path"][i - 1].index(0) if (self.problem_id == "puzzle8" and i > 0) else -1
            act = r["actions"][i - 1] if i > 0 else None
            if i > 0:
                cum_cost += cost_fn(r["path"][i - 1], act, s)
            if i == 0:
                lbl = p.format_start(s)
            else:
                lbl = p.format_step(act, i, i == len(r["path"]) - 1)
                if self.problem_id == "graph":
                    lbl += f" (Cost: {cum_cost})"
            frames.append({"state": s, "action": act, "hl": hl, "cost": cum_cost, "label": lbl})
        return frames

    def run_comparison(self):
        p = self.cur_problem()
        st = self.cur_start()
        rows = []
        for algo in ALGORITHMS.values():
            res = algo["run"](p, st)
            cost = compute_path_cost(p, res)
            rows.append({"algo": algo, "res": res, "cost": cost})
        valid_steps = [len(x["res"]["actions"]) for x in rows if x["res"]["found"]]
        valid_costs = [x["cost"] for x in rows if x["cost"] is not None]
        min_steps = min(valid_steps) if valid_steps else None
        min_cost = min(valid_costs) if valid_costs else None
        for x in rows:
            x["is_opt_steps"] = x["res"]["found"] and min_steps is not None and len(x["res"]["actions"]) == min_steps
            x["is_opt_cost"] = x["cost"] is not None and min_cost is not None and x["cost"] == min_cost
        self.compare_rows = rows

    def run_search(self, auto_play=True):
        self.playing = False
        self.play_accum = 0.0
        self.result = self.cur_algo()["run"](self.cur_problem(), self.cur_start())
        self.mode = "solution" if (self.result and self.result["found"]) else "search"
        self.idx = 0
        self.frames = self.build_frames()
        self.run_comparison()
        if auto_play and len(self.frames) > 1:
            self.playing = True

    def select_problem(self, prob_id):
        if self.problem_id == prob_id:
            return
        self.problem_id = prob_id
        self.run_search(auto_play=False)
        self.init_anim_positions()

    def select_algo(self, algo_id):
        self.algo_id = algo_id
        self.run_search(auto_play=False)

    def set_graph_preset(self, key):
        WeightedGraphProblem.set_preset(key)
        self.starts["graph"] = WeightedGraphProblem.default_start
        self.init_anim_positions()
        self.run_search(auto_play=False)

    def set_mode(self, mode):
        if not self.result or (mode == "solution" and not self.result["found"]):
            return
        self.playing = False
        self.mode = mode
        self.idx = 0
        self.frames = self.build_frames()

    def go_to(self, i):
        if not self.frames:
            return
        self.playing = False
        self.idx = max(0, min(len(self.frames) - 1, i))

    def toggle_play(self):
        if len(self.frames) <= 1:
            return
        if self.playing:
            self.playing = False
        else:
            if self.idx >= len(self.frames) - 1:
                self.idx = 0
            self.playing = True
            self.play_accum = 0.0

    def update(self, dt):
        self.dust_phase += dt * 2.2
        self.vortex_angle = (self.vortex_angle + dt * 360.0) % 360.0

        if self.playing and len(self.frames) > 1:
            self.play_accum += dt * 1000.0
            if self.play_accum >= self.speed_ms:
                self.play_accum -= self.speed_ms
                if self.idx < len(self.frames) - 1:
                    self.idx += 1
                else:
                    self.playing = False

        st = self.frames[self.idx]["state"] if self.frames else self.cur_start()
        k = 1.0 - math.exp(-12.0 * dt)
        if self.problem_id == "vacuum":
            target_x = 265.0 if st[0] == "A" else 635.0
            self.drone_x += (target_x - self.drone_x) * k
        elif self.problem_id == "puzzle8":
            for i, v in enumerate(st):
                if v == 0:
                    continue
                r, c = divmod(i, 3)
                if v not in self.tile_pos:
                    self.tile_pos[v] = [float(c), float(r)]
                self.tile_pos[v][0] += (c - self.tile_pos[v][0]) * k
                self.tile_pos[v][1] += (r - self.tile_pos[v][1]) * k
        else:
            pos_map = WeightedGraphProblem.preset()["pos"]
            if st in pos_map:
                tx, ty = pos_map[st]
                self.graph_cursor[0] += (tx - self.graph_cursor[0]) * k
                self.graph_cursor[1] += (ty - self.graph_cursor[1]) * k

    def render(self):
        s = self.screen
        s.fill(BG_PAGE)
        mx, my = pygame.mouse.get_pos()
        self.buttons = []

        # Header
        pygame.draw.line(s, BORDER, (24, 68), (W - 24, 68), 1)
        icon_rect = pygame.Rect(28, 16, 40, 40)
        draw_rounded_rect(s, icon_rect, PRIMARY, radius=10)
        pygame.draw.circle(s, CARD_BG, (48, 28), 4, 2)
        pygame.draw.circle(s, CARD_BG, (39, 44), 4, 2)
        pygame.draw.circle(s, CARD_BG, (57, 44), 4, 2)
        pygame.draw.line(s, CARD_BG, (46, 32), (41, 40), 2)
        pygame.draw.line(s, CARD_BG, (50, 32), (55, 40), 2)

        s.blit(self.f_title.render("AI Search Algorithms", True, TEXT_MAIN), (80, 14))
        s.blit(self.f_sub.render("Unified Interactive Problem & Algorithm Visualizer", True, TEXT_MUTED), (80, 40))

        # 3 Problem Tabs
        tab_bg = pygame.Rect(540, 16, 418, 40)
        draw_rounded_rect(s, tab_bg, SURFACE_SOFT, radius=10, border_color=BORDER)
        for idx, (pid, pcls) in enumerate(PROBLEMS.items()):
            r = pygame.Rect(544 + idx * 138, 20, 134, 32)
            active = (self.problem_id == pid)
            draw_button(
                s, r, pcls.name, self.f_btn,
                CARD_BG if active else SURFACE_SOFT,
                PRIMARY if active else TEXT_MUTED,
                hover=(not active and r.collidepoint(mx, my)), radius=7
            )
            self.buttons.append((r, lambda p=pid: self.select_problem(p)))

        algo = self.cur_algo()
        pill_rect = pygame.Rect(972, 20, 280, 32)
        draw_rounded_rect(s, pill_rect, algo["soft"], radius=16, border_color=algo["accent"])
        pill_txt = self.f_small.render(algo["badge"], True, algo["accent"])
        s.blit(pill_txt, pill_txt.get_rect(center=pill_rect.center))

        # Left Main Card
        left_card = pygame.Rect(24, 82, 856, 578)
        draw_rounded_rect(s, left_card, CARD_BG, radius=14, border_color=BORDER)

        s.blit(self.f_small.render("ALGORITHM", True, TEXT_MUTED), (44, 106))
        algo_bg = pygame.Rect(126, 96, 202, 34)
        draw_rounded_rect(s, algo_bg, SURFACE_SOFT, radius=8, border_color=BORDER)
        for idx, (aid, ainfo) in enumerate(ALGORITHMS.items()):
            r = pygame.Rect(130 + idx * 65, 100, 62, 26)
            active = (self.algo_id == aid)
            draw_button(
                s, r, ainfo["short"], self.f_btn,
                CARD_BG if active else SURFACE_SOFT,
                ainfo["accent"] if active else TEXT_MUTED,
                hover=(not active and r.collidepoint(mx, my)), radius=6
            )
            self.buttons.append((r, lambda a=aid: self.select_algo(a)))

        if self.problem_id == "vacuum":
            st = self.starts["vacuum"]
            s.blit(self.f_small.render("SETUP", True, TEXT_MUTED), (344, 106))
            r_pos = pygame.Rect(392, 97, 94, 32)
            draw_button(s, r_pos, f"Robot: {st[0]}", self.f_btn, SURFACE_SOFT, TEXT_MAIN, BORDER, r_pos.collidepoint(mx, my))
            self.buttons.append((r_pos, self.toggle_vac_pos))

            r_a = pygame.Rect(492, 97, 110, 32)
            draw_button(s, r_a, f"Room A: {st[1]}", self.f_body,
                        DIRTY_BG if st[1] == "Dirty" else CLEAN_BG,
                        DIRTY_TEXT if st[1] == "Dirty" else CLEAN_TEXT,
                        DIRTY_BORDER if st[1] == "Dirty" else CLEAN_BORDER, r_a.collidepoint(mx, my))
            self.buttons.append((r_a, self.toggle_vac_a))

            r_b = pygame.Rect(608, 97, 110, 32)
            draw_button(s, r_b, f"Room B: {st[2]}", self.f_body,
                        DIRTY_BG if st[2] == "Dirty" else CLEAN_BG,
                        DIRTY_TEXT if st[2] == "Dirty" else CLEAN_TEXT,
                        DIRTY_BORDER if st[2] == "Dirty" else CLEAN_BORDER, r_b.collidepoint(mx, my))
            self.buttons.append((r_b, self.toggle_vac_b))
        elif self.problem_id == "puzzle8":
            s.blit(self.f_small.render("PRESETS", True, TEXT_MUTED), (342, 106))
            r_p2 = pygame.Rect(404, 97, 74, 32)
            draw_button(s, r_p2, "2 Steps", self.f_body, SURFACE_SOFT, TEXT_MAIN, BORDER, r_p2.collidepoint(mx, my))
            self.buttons.append((r_p2, lambda: self.set_puzzle_start(Puzzle8Problem.default_start)))

            r_p6 = pygame.Rect(484, 97, 74, 32)
            draw_button(s, r_p6, "6 Steps", self.f_body, SURFACE_SOFT, TEXT_MAIN, BORDER, r_p6.collidepoint(mx, my))
            self.buttons.append((r_p6, lambda: self.set_puzzle_start(Puzzle8Problem.shuffled(6))))

            r_shuf = pygame.Rect(564, 97, 72, 32)
            draw_button(s, r_shuf, "Shuffle", self.f_body, SURFACE_SOFT, TEXT_MAIN, BORDER, r_shuf.collidepoint(mx, my))
            self.buttons.append((r_shuf, lambda: self.set_puzzle_start(Puzzle8Problem.shuffled(24))))

            inv = Puzzle8Problem.inversions(self.starts["puzzle8"])
            par_r = pygame.Rect(642, 100, 82, 26)
            draw_rounded_rect(s, par_r, CLEAN_BG, radius=13)
            pt = self.f_small.render(f"Valid ({inv})", True, CLEAN_TEXT)
            s.blit(pt, pt.get_rect(center=par_r.center))
        else:
            s.blit(self.f_small.render("GRAPH MAP", True, TEXT_MUTED), (344, 106))
            for g_i, (gkey, gdata) in enumerate(GRAPH_PRESETS.items()):
                gr = pygame.Rect(426 + g_i * 130, 97, 122, 32)
                active = (WeightedGraphProblem.active_preset == gkey)
                draw_button(
                    s, gr, gdata["name"], self.f_body,
                    PRIMARY_SOFT if active else SURFACE_SOFT,
                    PRIMARY if active else TEXT_MAIN,
                    PRIMARY if active else BORDER, gr.collidepoint(mx, my)
                )
                self.buttons.append((gr, lambda k=gkey: self.set_graph_preset(k)))

        r_run = pygame.Rect(732, 95, 128, 36)
        draw_button(s, r_run, "Run & Play", self.f_btn, PRIMARY, CARD_BG, hover=r_run.collidepoint(mx, my), radius=9)
        self.buttons.append((r_run, lambda: self.run_search(auto_play=True)))

        pygame.draw.line(s, BORDER, (44, 144), (860, 144), 1)

        # Arena
        arena_rect = pygame.Rect(44, 158, 816, 336)
        draw_rounded_rect(s, arena_rect, SURFACE_ARENA, radius=12, border_color=BORDER)

        cur_frame = self.frames[self.idx] if self.frames else {"state": self.cur_start(), "action": None, "hl": -1, "label": "Ready."}
        if self.problem_id == "vacuum":
            self.render_vacuum_arena(arena_rect, cur_frame)
        elif self.problem_id == "puzzle8":
            self.render_puzzle_arena(arena_rect, cur_frame)
        else:
            self.render_graph_arena(arena_rect, cur_frame)

        # Caption
        cap_rect = pygame.Rect(44, 506, 816, 38)
        draw_rounded_rect(s, cap_rect, SURFACE_SOFT, radius=8, border_color=BORDER)
        cap_txt = self.f_body.render(cur_frame["label"], True, TEXT_MAIN)
        s.blit(cap_txt, cap_txt.get_rect(center=cap_rect.center))

        # Playback Controls
        pb_btns = [
            ("<<", lambda: self.go_to(0)),
            ("<", lambda: self.go_to(self.idx - 1)),
            ("Pause" if self.playing else "Play", self.toggle_play),
            (">", lambda: self.go_to(self.idx + 1)),
            (">>", lambda: self.go_to(len(self.frames) - 1)),
        ]
        bx = 270
        for label, cb in pb_btns:
            is_play = label in ("Play", "Pause")
            bw = 66 if is_play else 42
            br = pygame.Rect(bx, 556, bw, 32)
            draw_button(
                s, br, label, self.f_btn,
                PRIMARY if is_play else SURFACE_SOFT,
                CARD_BG if is_play else TEXT_MAIN,
                None if is_play else BORDER,
                br.collidepoint(mx, my), radius=7
            )
            self.buttons.append((br, cb))
            bx += bw + 8

        n_frames = len(self.frames)
        cnt_str = f"{self.idx + 1} / {n_frames}" if n_frames else "—"
        s.blit(self.f_btn.render(cnt_str, True, TEXT_MUTED), (bx + 10, 563))

        self.scrub_rect = pygame.Rect(44, 600, 816, 12)
        pygame.draw.rect(s, BORDER, (44, 604, 816, 4), border_radius=2)
        ratio = (self.idx / max(1, n_frames - 1)) if n_frames > 1 else 0.0
        fill_w = int(816 * ratio)
        if fill_w > 0:
            pygame.draw.rect(s, PRIMARY, (44, 604, fill_w, 4), border_radius=2)
        knob_x = 44 + fill_w
        pygame.draw.circle(s, PRIMARY, (knob_x, 606), 7)
        pygame.draw.circle(s, CARD_BG, (knob_x, 606), 3)

        speed_opts = [(800, "0.5x"), (420, "1x"), (200, "2x"), (80, "4x")]
        s.blit(self.f_small.render("SPEED", True, TEXT_MUTED), (44, 628))
        sx = 95
        for ms_val, sp_lbl in speed_opts:
            sr = pygame.Rect(sx, 622, 42, 26)
            active = (self.speed_ms == ms_val)
            draw_button(
                s, sr, sp_lbl, self.f_small,
                PRIMARY_SOFT if active else SURFACE_SOFT,
                PRIMARY if active else TEXT_MUTED,
                PRIMARY if active else BORDER, sr.collidepoint(mx, my), radius=6
            )
            self.buttons.append((sr, lambda v=ms_val: setattr(self, "speed_ms", v)))
            sx += 48

        mode_bg = pygame.Rect(618, 620, 242, 30)
        draw_rounded_rect(s, mode_bg, SURFACE_SOFT, radius=8, border_color=BORDER)
        for idx, (m_id, m_lbl) in enumerate([("solution", "Solution Path"), ("search", "Search Trace")]):
            mr = pygame.Rect(622 + idx * 118, 623, 116, 24)
            active = (self.mode == m_id)
            draw_button(
                s, mr, m_lbl, self.f_small,
                CARD_BG if active else SURFACE_SOFT,
                PRIMARY if active else TEXT_MUTED,
                hover=(not active and mr.collidepoint(mx, my)), radius=6
            )
            self.buttons.append((mr, lambda m=m_id: self.set_mode(m)))

        # Right Metrics & History Card
        right_card = pygame.Rect(896, 82, 360, 578)
        draw_rounded_rect(s, right_card, CARD_BG, radius=14, border_color=BORDER)
        s.blit(self.f_h2.render("Execution Metrics", True, TEXT_MAIN), (916, 100))

        r = self.result
        if r:
            status_lbl = "Solved" if r["found"] else ("Aborted" if r["aborted"] else "Failed")
            st_bg = CLEAN_BG if r["found"] else DIRTY_BG
            st_fg = CLEAN_TEXT if r["found"] else DIRTY_TEXT
        else:
            status_lbl, st_bg, st_fg = "Ready", SURFACE_SOFT, TEXT_MUTED
        st_rect = pygame.Rect(1176, 98, 62, 24)
        draw_rounded_rect(s, st_rect, st_bg, radius=12)
        st_txt = self.f_small.render(status_lbl, True, st_fg)
        s.blit(st_txt, st_txt.get_rect(center=st_rect.center))

        total_cost = compute_path_cost(self.cur_problem(), r) if r else None
        metrics = [
            ("Solution Steps", str(len(r["actions"])) if (r and r["found"]) else "—", PRIMARY),
            ("Total Cost", str(total_cost) if total_cost is not None else "—", UCS_ACCENT),
            ("Expanded", f"{r['expanded']:,}" if r else "—", TEXT_MAIN),
            ("Generated", f"{r['generated']:,}" if r else "—", TEXT_MAIN),
            ("Max Frontier", f"{r['max_frontier']:,}" if r else "—", TEXT_MAIN),
            ("Runtime", f"{r['ms']:.2f} ms" if r else "—", TEXT_MAIN),
        ]
        for idx, (m_lbl, m_val, m_col) in enumerate(metrics):
            col_i, row_i = idx % 2, idx // 2
            mr = pygame.Rect(916 + col_i * 164, 136 + row_i * 62, 156, 54)
            draw_rounded_rect(s, mr, SURFACE_SOFT, radius=9, border_color=BORDER)
            s.blit(self.f_small.render(m_lbl, True, TEXT_MUTED), (mr.x + 10, mr.y + 8))
            s.blit(self.f_metric.render(m_val, True, m_col), (mr.x + 10, mr.y + 25))

        s.blit(self.f_h2.render("Step History", True, TEXT_MAIN), (916, 332))
        log_box = pygame.Rect(916, 360, 320, 282)
        draw_rounded_rect(s, log_box, SURFACE_SOFT, radius=10, border_color=BORDER)

        if self.frames:
            max_vis = 8
            start_i = max(0, min(self.idx - 3, len(self.frames) - max_vis))
            for row_k, fi in enumerate(range(start_i, min(len(self.frames), start_i + max_vis))):
                item_r = pygame.Rect(924, 368 + row_k * 33, 304, 29)
                is_cur = (fi == self.idx)
                if is_cur:
                    draw_rounded_rect(s, item_r, CARD_BG, radius=6, border_color=BORDER)
                txt = f"{fi + 1}. {self.frames[fi]['label']}"
                if len(txt) > 40:
                    txt = txt[:37] + "..."
                s.blit(self.f_body.render(txt, True, PRIMARY if is_cur else TEXT_MUTED), (item_r.x + 8, item_r.y + 5))

        # Bottom Comparison Benchmark Card (Fits 3 Algorithms cleanly)
        comp_card = pygame.Rect(24, 676, W - 48, 174)
        draw_rounded_rect(s, comp_card, CARD_BG, radius=14, border_color=BORDER)
        s.blit(self.f_h2.render("Algorithm Performance Comparison (Click a row to load)", True, TEXT_MAIN), (44, 688))

        r_ref = pygame.Rect(1136, 684, 100, 28)
        draw_button(s, r_ref, "Refresh", self.f_small, SURFACE_SOFT, TEXT_MAIN, BORDER, r_ref.collidepoint(mx, my), radius=7)
        self.buttons.append((r_ref, self.run_comparison))

        cols = [("Algorithm", 44), ("Data Structure", 240), ("Found", 410),
                ("Steps", 500), ("Total Cost", 640), ("Expanded", 780),
                ("Generated", 900), ("Max Frontier", 1020), ("Runtime", 1150)]
        pygame.draw.rect(s, SURFACE_SOFT, (44, 718, W - 88, 26), border_radius=6)
        for cname, cx in cols:
            s.blit(self.f_small.render(cname.upper(), True, TEXT_MUTED), (cx + 6, 724))

        self.compare_rects = []
        for r_i, row in enumerate(self.compare_rows):
            ry = 748 + r_i * 31
            row_rect = pygame.Rect(44, ry, W - 88, 27)
            a = row["algo"]
            is_sel = (a["id"] == self.algo_id)
            if is_sel:
                draw_rounded_rect(s, row_rect, a["soft"], radius=6)
            elif row_rect.collidepoint(mx, my):
                draw_rounded_rect(s, row_rect, SURFACE_SOFT, radius=6)

            res = row["res"]
            steps_txt = f"{len(res['actions']):,}" + (" (Min)" if row["is_opt_steps"] else "") if res["found"] else "—"
            cost_txt = f"{row['cost']:,}" + (" (Optimal)" if row["is_opt_cost"] else "") if row["cost"] is not None else "—"
            vals = [
                (a["name"], 44, a["accent"] if is_sel else TEXT_MAIN, True),
                (a["structure"], 240, TEXT_MUTED, False),
                ("Yes" if res["found"] else "No", 410, CLEAN_TEXT if res["found"] else DIRTY_TEXT, True),
                (steps_txt, 500, PRIMARY if row["is_opt_steps"] else TEXT_MAIN, row["is_opt_steps"]),
                (cost_txt, 640, CLEAN_TEXT if row["is_opt_cost"] else TEXT_MAIN, row["is_opt_cost"]),
                (f"{res['expanded']:,}", 780, TEXT_MAIN, False),
                (f"{res['generated']:,}", 900, TEXT_MAIN, False),
                (f"{res['max_frontier']:,}", 1020, TEXT_MAIN, False),
                (f"{res['ms']:.2f} ms", 1150, TEXT_MUTED, False),
            ]
            for val, vx, vc, bold in vals:
                fnt = self.f_btn if bold else self.f_body
                s.blit(fnt.render(val, True, vc), (vx + 6, ry + 4))
            self.compare_rects.append((row_rect, a["id"]))

        pygame.display.flip()

    def render_vacuum_arena(self, arena, frame):
        s = self.screen
        st = frame["state"]
        act = frame["action"]

        pygame.draw.rect(s, (216, 209, 196), (arena.centerx - 22, arena.centery - 40, 44, 80), border_radius=4)
        rooms = [("Room A", st[1], pygame.Rect(68, 180, 368, 290)),
                 ("Room B", st[2], pygame.Rect(468, 180, 368, 290))]

        for title, status, rr in rooms:
            dirty = (status == "Dirty")
            draw_rounded_rect(s, rr, DIRTY_BG if dirty else CLEAN_BG, radius=14,
                              border_color=DIRTY_BORDER if dirty else CLEAN_BORDER, border_width=2)
            for gx in range(rr.x + 22, rr.right - 16, 26):
                for gy in range(rr.y + 52, rr.bottom - 16, 26):
                    pygame.draw.circle(s, (200, 190, 175), (gx, gy), 1)

            s.blit(self.f_h2.render(title, True, TEXT_MAIN), (rr.x + 18, rr.y + 16))
            badge_r = pygame.Rect(rr.right - 88, rr.y + 14, 70, 24)
            draw_rounded_rect(s, badge_r, (244, 216, 186) if dirty else (210, 235, 218), radius=12)
            bt = self.f_small.render(status, True, DIRTY_TEXT if dirty else CLEAN_TEXT)
            s.blit(bt, bt.get_rect(center=badge_r.center))

            if dirty:
                offsets = [(90, 110), (260, 195), (110, 225), (245, 95)]
                for idx_d, (ox, oy) in enumerate(offsets):
                    dx = ox + math.sin(self.dust_phase + idx_d) * 5
                    dy = oy + math.cos(self.dust_phase + idx_d * 1.3) * 5
                    pygame.draw.circle(s, (194, 97, 32), (int(rr.x + dx), int(rr.y + dy)), 5)

        cx, cy = int(self.drone_x), arena.centery + 12
        if act == "Suck":
            for i in range(6):
                ang = math.radians(self.vortex_angle + i * 60)
                pygame.draw.circle(s, PRIMARY, (cx + int(math.cos(ang) * 56), cy + int(math.sin(ang) * 56)), 4)

        pygame.draw.circle(s, (205, 198, 186), (cx, cy + 6), 44)
        pygame.draw.circle(s, (50, 48, 45), (cx, cy), 43)
        pygame.draw.circle(s, CARD_BG, (cx, cy), 35)
        pygame.draw.arc(s, PRIMARY, (cx - 35, cy - 35, 70, 70), 0.5, 2.64, 4)
        pygame.draw.circle(s, PRIMARY_SOFT, (cx, cy), 14)
        pygame.draw.circle(s, PRIMARY, (cx, cy), 14, 2)
        pygame.draw.circle(s, PRIMARY, (cx, cy), 5)

    def render_puzzle_arena(self, arena, frame):
        s = self.screen
        st = frame["state"]
        hl = frame["hl"]

        tw, gap = 86, 8
        step = tw + gap
        board_w = tw * 3 + gap * 2
        bx = arena.centerx - board_w // 2
        by = arena.centery - board_w // 2

        tray = pygame.Rect(bx - 12, by - 12, board_w + 24, board_w + 24)
        draw_rounded_rect(s, tray, (216, 209, 196), radius=16, border_color=BORDER_DARK)

        for r in range(3):
            for c in range(3):
                sr = pygame.Rect(bx + c * step, by + r * step, tw, tw)
                draw_rounded_rect(s, sr, (238, 234, 224), radius=10, border_color=(200, 192, 178))

        for i, v in enumerate(st):
            if v == 0:
                continue
            gx, gy = self.tile_pos.get(v, (i % 3, i // 3))
            tx, ty = round(bx + gx * step), round(by + gy * step)

            is_locked = (v == Puzzle8Problem.goal[i])
            is_moved = (i == hl)

            if is_moved:
                bg, lip, bcol, fg = TILE_MOVED_BG, (165, 180, 252), TILE_MOVED_BORDER, PRIMARY
            elif is_locked:
                bg, lip, bcol, fg = TILE_LOCKED_BG, TILE_LOCKED_LIP, CLEAN_BORDER, CLEAN_TEXT
            else:
                bg, lip, bcol, fg = TILE_BG, TILE_LIP, BORDER_DARK, TEXT_MAIN

            pygame.draw.rect(s, lip, (tx, ty + 3, tw, tw), border_radius=10)
            tile_r = pygame.Rect(tx, ty, tw, tw)
            draw_rounded_rect(s, tile_r, bg, radius=10, border_color=bcol, border_width=2)
            if is_locked:
                pygame.draw.circle(s, CLEAN_TEXT, (tx + tw - 11, ty + 11), 3)
            lbl = self.f_tile.render(str(v), True, fg)
            s.blit(lbl, lbl.get_rect(center=tile_r.center))

    def render_graph_arena(self, arena, frame):
        s = self.screen
        preset = WeightedGraphProblem.preset()
        pos_map = preset["pos"]
        cur_node = frame["state"]
        accent = self.cur_algo()["accent"]
        soft = self.cur_algo()["soft"]

        def to_px(nx, ny):
            return int(arena.x + 56 + nx * (arena.w - 112)), int(arena.y + 38 + ny * (arena.h - 76))

        # Active path edges up to current frame
        active_edges = set()
        if self.mode == "solution" and self.result and self.result["found"]:
            path = self.result["path"]
            for i in range(min(self.idx, len(path) - 1)):
                u, v = path[i], path[i + 1]
                active_edges.add((u, v))
                active_edges.add((v, u))

        visited_nodes = set()
        if self.mode == "search" and self.frames:
            for k in range(self.idx + 1):
                visited_nodes.add(self.frames[k]["state"])
        elif self.mode == "solution" and self.result and self.result["found"]:
            for k in range(min(self.idx + 1, len(self.result["path"]))):
                visited_nodes.add(self.result["path"][k])

        # Draw edges and weight badges
        for u, v, w in preset["edges"]:
            p1 = to_px(*pos_map[u])
            p2 = to_px(*pos_map[v])
            is_active = (u, v) in active_edges
            pygame.draw.line(s, accent if is_active else BORDER_DARK, p1, p2, 5 if is_active else 2)

            mx, my = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
            w_rect = pygame.Rect(mx - 14, my - 11, 28, 22)
            draw_rounded_rect(s, w_rect, soft if is_active else CARD_BG, radius=6,
                              border_color=accent if is_active else BORDER_DARK, border_width=1)
            wt = self.f_small.render(str(w), True, accent if is_active else TEXT_MAIN)
            s.blit(wt, wt.get_rect(center=w_rect.center))

        # Smooth focus halo around current node
        hx, hy = to_px(*self.graph_cursor)
        pygame.draw.circle(s, soft, (hx, hy), 30)
        pygame.draw.circle(s, accent, (hx, hy), 30, 2)

        # Draw nodes
        for name, (nx, ny) in pos_map.items():
            px, py = to_px(nx, ny)
            is_cur = (name == cur_node)
            is_start = (name == preset["start"])
            is_goal = (name == preset["goal"])
            is_vis = (name in visited_nodes)

            if is_cur:
                bg, bd, fg = accent, accent, CARD_BG
            elif is_goal:
                bg, bd, fg = CLEAN_BG, CLEAN_BORDER, CLEAN_TEXT
            elif is_vis:
                bg, bd, fg = soft, accent, accent
            else:
                bg, bd, fg = CARD_BG, BORDER_DARK, TEXT_MAIN

            pygame.draw.circle(s, (200, 193, 180), (px, py + 3), 23)
            pygame.draw.circle(s, bg, (px, py), 23)
            pygame.draw.circle(s, bd, (px, py), 23, 2)

            short_lbl = name[:4] if len(name) > 4 else name
            nt = self.f_btn.render(short_lbl, True, fg)
            s.blit(nt, nt.get_rect(center=(px, py)))

            if is_start or is_goal:
                tag = "START" if is_start else "GOAL"
                t_col = PRIMARY if is_start else CLEAN_TEXT
                tt = self.f_small.render(tag, True, t_col)
                s.blit(tt, tt.get_rect(center=(px, py - 32)))

    def toggle_vac_pos(self):
        p, a, b = self.starts["vacuum"]
        self.starts["vacuum"] = ("B" if p == "A" else "A", a, b)
        self.run_search(auto_play=False)

    def toggle_vac_a(self):
        p, a, b = self.starts["vacuum"]
        self.starts["vacuum"] = (p, "Clean" if a == "Dirty" else "Dirty", b)
        self.run_search(auto_play=False)

    def toggle_vac_b(self):
        p, a, b = self.starts["vacuum"]
        self.starts["vacuum"] = (p, a, "Clean" if b == "Dirty" else "Dirty")
        self.run_search(auto_play=False)

    def set_puzzle_start(self, val):
        self.starts["puzzle8"] = val
        self.run_search(auto_play=False)

    def scrub_to_mouse(self, mx):
        if not self.frames:
            return
        ratio = max(0.0, min(1.0, (mx - self.scrub_rect.x) / max(1, self.scrub_rect.w)))
        self.go_to(round(ratio * (len(self.frames) - 1)))

    def run(self):
        running = True
        prob_keys = list(PROBLEMS.keys())
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mx, my = ev.pos
                    if self.scrub_rect.inflate(10, 14).collidepoint(mx, my):
                        self.dragging_scrub = True
                        self.scrub_to_mouse(mx)
                        continue
                    for rect, cb in self.buttons:
                        if rect.collidepoint(mx, my):
                            cb()
                            break
                    for rect, aid in self.compare_rects:
                        if rect.collidepoint(mx, my):
                            self.select_algo(aid)
                            break
                elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                    self.dragging_scrub = False
                elif ev.type == pygame.MOUSEMOTION and self.dragging_scrub:
                    self.scrub_to_mouse(ev.pos[0])
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_SPACE:
                        self.toggle_play()
                    elif ev.key == pygame.K_RIGHT:
                        self.go_to(self.idx + 1)
                    elif ev.key == pygame.K_LEFT:
                        self.go_to(self.idx - 1)
                    elif ev.key == pygame.K_TAB:
                        nxt_i = (prob_keys.index(self.problem_id) + 1) % len(prob_keys)
                        self.select_problem(prob_keys[nxt_i])

            self.update(dt)
            self.render()

        pygame.quit()


if __name__ == "__main__":
    App().run()
