"""
Module: 2. Training Pipeline
Author: Forked
Date: 2026-02-09
Purpose: Implements the benchmark edge id module for experimental training or agent-development workflows related to the project's learning pipeline.
"""

import timeit

result = timeit.timeit("tuple(sorted((a,b)))", setup="a = 20; b = 45", number=2_000_000)
print("TODAY", result)

result = timeit.timeit(
    "(a,b) if a < b else (b,a)", setup="a = 20; b = 45", number=2_000_000
)
print("TERNARY", result)

result = timeit.timeit(
    "edge_id((a, b))",
    setup="a = 20; b = 45; edge_id = lambda x: (x[0],x[1]) if x[0] < x[1] else (x[1],x[0])",
    number=2_000_000,
)
print("FUNC TERNARY", result)

result = timeit.timeit(
    "edge_id(a, b)",
    setup="a = 20; b = 45; edge_id = lambda x, y: (x,y) if x < y else (y,x)",
    number=2_000_000,
)
print("FUNC TERNARY 2 PARAMS", result)

result = timeit.timeit(
    "(min(a, b), max(a, b))", setup="a = 20; b = 45", number=2_000_000
)
print("MIN MAX", result)

# I like map lookup because makes it easy to change to INT ids in the future (a more
# compact representation of an edge)
result = timeit.timeit(
    "edge_id[(a,b)]", setup="a = 20; b = 45; edge_id = {(a,b): 1}", number=2_000_000
)
print("MAP LOOKUP", result)
