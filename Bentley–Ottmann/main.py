import random

from bentley_ottmann import BentleyOttmann
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


def generate_point(max_xy):
    return random.randint(0, max_xy), random.randint(0, max_xy)


def segments_generator(n, max_xy):
    for _ in range(n):
        p1 = generate_point(max_xy)
        p2 = generate_point(max_xy)
        if p2[0] < p1[0]:
            p2, p1 = p1, p2
        elif p2[0] == p1[0] and p2[1] < p1[1]:
            p2, p1 = p1, p2
        yield p1, p2


def main():
    v = Plot()
    segments = list(segments_generator(5, 1000))
    print(segments)
    for s in segments:
        v.add_segment(s[0], s[1])

    bo = BentleyOttmann(segments)
    intersections = bo.find_intersections()
    for p in intersections:
        v.add_point(p)
    v.show()


if __name__ == "__main__":
    main()
