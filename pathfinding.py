# Task 3: Heuristic Grid Pathfinding (Dijkstra and A*), code as run in Google Colab

# ---- Step 1: build a grid maze
import numpy as np
import matplotlib.pyplot as plt

def make_grid(size=30, obstacle_ratio=0.25, seed=0):
    rng = np.random.default_rng(seed)
    grid = (rng.random((size, size)) < obstacle_ratio).astype(int)  # 1 = wall, 0 = free
    grid[0, 0] = grid[size - 1, size - 1] = 0                        # keep start and goal free
    return grid

def show(grid, title="Grid maze"):
    plt.figure(figsize=(5, 5))
    plt.imshow(grid, cmap="Greys")
    plt.scatter([0], [0], c="green", s=80, label="Start")
    plt.scatter([grid.shape[1] - 1], [grid.shape[0] - 1], c="red", s=80, label="Goal")
    plt.title(title); plt.legend(loc="upper right"); plt.xticks([]); plt.yticks([])
    plt.show()

grid = make_grid(30, 0.25)
print("Grid size:", grid.shape, "| walls:", grid.sum(), "| free cells:", (grid == 0).sum())
show(grid, "30x30 maze, 25% walls")

# ---- Step 2: Dijkstra and A* from scratch (with tie-breaking)
import heapq, time

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def search(grid, start, goal, use_heuristic=True):
    """A* when use_heuristic=True, Dijkstra when False. Moves: up, down, left, right."""
    t0 = time.perf_counter()
    rows, cols = grid.shape
    open_list = [(0, 0, start)]           # priority queue of (priority, tie-breaker, cell)
    came_from = {start: None}             # to rebuild the path at the end
    cost = {start: 0}                     # steps from start to each cell
    expanded = []                         # cells we fully explored (in order)
    done = set()
    while open_list:
        _, _, cell = heapq.heappop(open_list)
        if cell in done:
            continue
        done.add(cell)
        expanded.append(cell)
        if cell == goal:
            break
        r, c = cell
        for nr, nc in [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]:
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr, nc] == 0:
                new_cost = cost[cell] + 1
                if new_cost < cost.get((nr, nc), float("inf")):
                    cost[(nr, nc)] = new_cost
                    came_from[(nr, nc)] = cell
                    h = manhattan((nr, nc), goal) if use_heuristic else 0
                    heapq.heappush(open_list, (new_cost + h, h, (nr, nc)))
    path = []
    if goal in came_from:                 # walk backwards from goal to start
        node = goal
        while node is not None:
            path.append(node)
            node = came_from[node]
        path.reverse()
    runtime_ms = (time.perf_counter() - t0) * 1000
    return path, expanded, runtime_ms
start, goal = (0, 0), (grid.shape[0] - 1, grid.shape[1] - 1)
for name, h in [("Dijkstra", False), ("A*", True)]:
    path, expanded, ms = search(grid, start, goal, use_heuristic=h)
    print(f"{name:9s} path steps={len(path) - 1:3d} | nodes expanded={len(expanded):4d} | runtime={ms:.2f} ms")

# ---- Step 3: test on 45 mazes and export a log
import pandas as pd

results = []
for size in [20, 40, 60]:
    for ratio in [0.10, 0.20, 0.30]:
        seed, kept = 0, 0
        while kept < 5:                              # 5 solvable mazes per setting
            g = make_grid(size, ratio, seed)
            s, t = (0, 0), (size - 1, size - 1)
            seed += 1
            if not search(g, s, t)[0]:               # no path exists: skip this maze
                continue
            kept += 1
            for name, h in [("Dijkstra", False), ("A*", True)]:
                path, expanded, ms = search(g, s, t, use_heuristic=h)
                results.append({"size": size, "obstacles_%": int(ratio * 100), "seed": seed - 1, "algorithm": name,
                                "steps": len(path) - 1, "expanded": len(expanded),
                                "density_%": round(100 * len(expanded) / (g == 0).sum(), 1),
                                "runtime_ms": round(ms, 3)})

df = pd.DataFrame(results)
df.to_csv("pathfinding_log.csv", index=False)        # exported log of every run
summary = df.groupby(["size", "obstacles_%", "algorithm"])[["steps", "expanded", "density_%", "runtime_ms"]].mean().round(2)
print(summary)

# ---- Step 4: visualizations
# Picture 1: what each algorithm explored, and the path it found
def draw_search(ax, g, path, expanded, title):
    img = np.ones((*g.shape, 3))                 # white = open
    img[g == 1] = [0.15, 0.15, 0.15]             # dark = wall
    for r, c in expanded:
        img[r, c] = [0.68, 0.85, 1.0]            # light blue = checked
    for r, c in path:
        img[r, c] = [1.0, 0.55, 0.0]             # orange = final path
    ax.imshow(img)
    ax.scatter([0], [0], c="green", s=60); ax.scatter([g.shape[1] - 1], [g.shape[0] - 1], c="red", s=60)
    ax.set_title(title, fontsize=10); ax.set_xticks([]); ax.set_yticks([])

s, t = (0, 0), (39, 39)
seed = 0
while not search(make_grid(40, 0.30, seed), s, t)[0]:   # pick the first maze that has a path
    seed += 1
g = make_grid(40, 0.30, seed)
fig, axes = plt.subplots(1, 2, figsize=(10, 5))
for ax, (name, h) in zip(axes, [("Dijkstra", False), ("A*", True)]):
    path, expanded, ms = search(g, s, t, use_heuristic=h)
    draw_search(ax, g, path, expanded, f"{name}: {len(path)-1} steps, {len(expanded)} nodes expanded")
plt.suptitle("Blue = squares checked, orange = shortest path")
plt.tight_layout(); plt.savefig("path_comparison.png", dpi=200); plt.show()

# Picture 2: average nodes expanded and runtime for each maze size
avg = df.groupby(["size", "algorithm"])[["expanded", "runtime_ms"]].mean().unstack()
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
avg["expanded"].plot(kind="bar", ax=axes[0], rot=0, color=["#1f77b4", "#ff7f0e"])
axes[0].set_title("Average nodes expanded"); axes[0].set_xlabel("Grid size (N x N)")
avg["runtime_ms"].plot(kind="bar", ax=axes[1], rot=0, color=["#1f77b4", "#ff7f0e"])
axes[1].set_title("Average runtime (ms)"); axes[1].set_xlabel("Grid size (N x N)")
plt.tight_layout(); plt.savefig("metrics_by_size.png", dpi=200); plt.show()

# Picture 3: how wall density changes the search
dens = df.groupby(["obstacles_%", "algorithm"])["density_%"].mean().unstack()
dens.plot(marker="o", figsize=(6, 4), color=["#1f77b4", "#ff7f0e"])
plt.title("Share of open squares checked"); plt.xlabel("Walls (%)"); plt.ylabel("Squares checked (%)")
plt.ylim(0, 105); plt.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("density_by_obstacles.png", dpi=200); plt.show()
