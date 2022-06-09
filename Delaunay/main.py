import random
import numpy as np
from delaunay import Delaunay
import matplotlib.pyplot as plt


class Plot:
    def __init__(self):
        self.segments = []
        self.points = []

    def add_segment(self, p1, p2):
        self.segments.append([p1[0], p2[0]])
        self.segments.append([p1[1], p2[1]])

    def add_point(self, p):
        self.points.append(p)

    def show(self):
        plt.plot(*self.segments)
        plt.plot([p[0] for p in self.points], [p[1] for p in self.points], '.')
        plt.show()


def main():
    v = Plot()
    seeds = list(map(lambda p: p * 10, np.random.random((10, 2))))

    dt = Delaunay()
    for s in seeds:
        dt.addPoint(s)
        v.add_point(s)

    print("Input points:\n", seeds)
    print("Delaunay triangles:\n", dt.exportTriangles())

    triangles = dt.exportTriangles()
    for triangle in triangles:
        v.add_segment(seeds[triangle[0]], seeds[triangle[1]])
        v.add_segment(seeds[triangle[1]], seeds[triangle[2]])
        v.add_segment(seeds[triangle[2]], seeds[triangle[0]])

    v.show()


if __name__ == "__main__":
    main()
