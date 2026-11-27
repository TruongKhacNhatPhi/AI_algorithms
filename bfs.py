import time
from collections import deque


class Node:
    def __init__(self, state, parent=None, action=None, depth=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.depth = depth


def solution(node):
    path, actions = [], []
    curr = node
    while curr is not None:
        path.append(curr.state)
        if curr.action is not None:
            actions.append(curr.action)
        curr = curr.parent
    path.reverse()
    actions.reverse()
    return path, actions


def BFS(problem, start, max_expand=300000):
    t0 = time.perf_counter()
    start_node = Node(start)
    trace = []
    generated = 1
    max_frontier = 1
    goal_node = None
    aborted = False

    if problem.is_goal(start):
        goal_node = start_node
    else:
        frontier = deque([start_node])
        in_frontier = {start}
        explored = set()

        while frontier:
            node = frontier.popleft()
            st = node.state
            in_frontier.discard(st)
            explored.add(st)

            trace.append({
                "state": st,
                "action": node.action,
                "depth": node.depth,
                "frontier_size": len(frontier),
                "explored_size": len(explored),
            })

            if len(trace) >= max_expand:
                aborted = True
                break

            found_goal = False
            for action in problem.actions(st):
                ns = problem.result(st, action)
                if ns in explored or ns in in_frontier:
                    continue
                generated += 1
                child = Node(ns, parent=node, action=action, depth=node.depth + 1)
                if problem.is_goal(ns):
                    goal_node = child
                    found_goal = True
                    break
                frontier.append(child)
                in_frontier.add(ns)

            if found_goal:
                break
            max_frontier = max(max_frontier, len(frontier))

    path, actions = solution(goal_node) if goal_node else ([], [])
    return {
        "found": goal_node is not None,
        "aborted": aborted,
        "path": path,
        "actions": actions,
        "trace": trace,
        "expanded": len(trace),
        "generated": generated,
        "max_frontier": max_frontier,
        "ms": (time.perf_counter() - t0) * 1000.0,
    }
