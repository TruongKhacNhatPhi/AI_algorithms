import heapq
import time


class Node:
    def __init__(self, state, parent=None, action=None, depth=0, cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.depth = depth
        self.cost = cost


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


def UCS(problem, start, max_expand=300000):
    t0 = time.perf_counter()
    start_node = Node(start, depth=0, cost=0)
    trace = []
    generated = 1
    max_frontier = 1
    goal_node = None
    aborted = False

    counter = 0
    frontier = [(0, counter, start_node)]
    best_cost = {start: 0}
    explored = set()
    step_cost_fn = getattr(problem, "step_cost", lambda s, a, ns: 1)

    while frontier:
        cost, _, node = heapq.heappop(frontier)
        st = node.state

        if st in explored or cost > best_cost.get(st, float("inf")):
            continue

        explored.add(st)
        trace.append({
            "state": st,
            "action": node.action,
            "depth": node.depth,
            "cost": cost,
            "frontier_size": len(frontier),
            "explored_size": len(explored),
        })

        if problem.is_goal(st):
            goal_node = node
            break

        if len(trace) >= max_expand:
            aborted = True
            break

        for action in problem.actions(st):
            ns = problem.result(st, action)
            if ns in explored:
                continue
            new_cost = cost + step_cost_fn(st, action, ns)
            if new_cost < best_cost.get(ns, float("inf")):
                best_cost[ns] = new_cost
                generated += 1
                counter += 1
                child = Node(ns, parent=node, action=action, depth=node.depth + 1, cost=new_cost)
                heapq.heappush(frontier, (new_cost, counter, child))

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
        "cost": goal_node.cost if goal_node else None,
        "ms": (time.perf_counter() - t0) * 1000.0,
    }
