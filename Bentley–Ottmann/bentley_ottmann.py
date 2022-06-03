from enum import Enum
from functools import total_ordering
from heapq import heappush, heapify, heappop

from shapely.geometry import LineString
from shapely.geometry import Point as SPoint

from tree import AVLTree, Node


class PointType(Enum):
    nothing = 0
    cross = 1
    start = 2
    end = 3


@total_ordering
class Point(SPoint):
    segment_relation = PointType.nothing
    segment = None

    def set_segment(self, s, is_start=True):
        self.segment = s
        if is_start:
            self.segment_relation = PointType.start
        else:
            self.segment_relation = PointType.end

    def set_cross_segment(self, s1, s2):
        if s1 > s2:
            s1, s2 = s2, s1
        self.segment = s1
        self.cross_segment = s2
        self.segment_relation = PointType.cross

    def __gt__(self, other):
        if self.x > other.x:
            return True
        elif self.x == other.x and self.y > other.y:
            return True
        return False

    def __eq__(self, other):
        if self.x == other.x and self.y == other.y:
            return True
        return False

    def __str__(self):
        return str(self.x) + "," + str(self.y)

    def __repr__(self):
        return self.__str__()


@total_ordering
class Segment(LineString):

    def __init__(self, coordinates=None):
        super().__init__(coordinates)
        self.sx = None

    def __gt__(self, other):
        max_x = max(self.sx, other.sx)
        self_p = self.find_y(max_x)
        other_p = other.find_y(max_x)
        if self_p.almost_equals(other_p):
            max_x = max(self.coords[0][0], other.coords[0][0])
            self_p = self.find_y(max_x)
            other_p = other.find_y(max_x)
        return self_p.y > other_p.y

    def __eq__(self, other):
        return self.almost_equals(other)

    def __str__(self):
        return "[" + str(self.coords[0]) + "," + str(self.coords[1]) + "]"

    def __repr__(self):
        return self.__str__()

    def find_y(self, x):
        h_line = LineString([(x, 0), (x, max(self.xy[1]))])
        intersection = self.intersection(h_line)
        if isinstance(intersection, LineString):
            intersection = Point(intersection.coords[0])
        return intersection


class BentleyOttmann:

    def __init__(self, xy_pairs):
        self.result = []
        self.event_points = []
        self.tree = AVLTree()
        for xy_pair in xy_pairs:
            start_point = Point(xy_pair[0])
            end_point = Point(xy_pair[1])
            segment = Segment([start_point, end_point])
            start_point.set_segment(segment, True)
            end_point.set_segment(segment, False)
            heappush(self.event_points, start_point)
            heappush(self.event_points, end_point)

    def find_intersections(self):
        while len(self.event_points):
            self.process_point(heappop(self.event_points))
        return self.result

    def try_add_intersect(self, seg1, seg2, sx):
        if seg1 is None or seg2 is None:
            return
        if isinstance(seg1, Node):
            seg1 = seg1.key
        if isinstance(seg2, Node):
            seg2 = seg2.key
        if seg1.intersects(seg2):
            cross_point = Point(seg1.intersection(seg2))
            cross_point.set_cross_segment(seg1, seg2)
            if cross_point.x <= sx:
                return None
            heappush(self.event_points, cross_point)
            return cross_point
        return None

    def try_remove_intersect(self, seg1, seg2, sx):
        if seg1 is None or seg2 is None:
            return
        if isinstance(seg1, Node):
            seg1 = seg1.key
        if isinstance(seg2, Node):
            seg2 = seg2.key
        if seg1.intersects(seg2):
            cross_point = seg1.intersection(seg2)
            if cross_point.x <= sx:
                return None
            try:
                self.event_points.remove(cross_point)
                return cross_point
            except Exception as e:
                pass
            heapify(self.event_points)
        return None

    def process_point(self, p):
        self.tree.sweep_line_x = p.x
        if p.segment_relation == PointType.start:
            self.process_start_point(p)
        elif p.segment_relation == PointType.end:
            self.process_end_point(p)
        elif p.segment_relation == PointType.cross:
            self.process_cross_point(p)

    def process_start_point(self, p):
        segment_node = self.tree.insert(p.segment)
        below_segment = self.tree.get_left(segment_node)
        above_segment = self.tree.get_right(segment_node)
        self.try_remove_intersect(below_segment, above_segment, p.x)
        self.try_add_intersect(p.segment, below_segment, p.x)
        self.try_add_intersect(p.segment, above_segment, p.x)

    def process_cross_point(self, p):
        self.result.append((p.x, p.y))
        segment1_node = self.tree.find(p.segment)
        segment2_node = self.tree.find(p.cross_segment)
        below_segment = self.tree.get_left(segment1_node)
        above_segment = self.tree.get_right(segment2_node)
        self.try_remove_intersect(above_segment, segment2_node, p.x)
        self.try_remove_intersect(below_segment, segment1_node, p.x)
        self.try_add_intersect(above_segment, segment1_node, p.x)
        self.try_add_intersect(below_segment, segment2_node, p.x)
        segment1_node.key, segment2_node.key = segment2_node.key, segment1_node.key

    def process_end_point(self, p):
        segment_node = self.tree.find(p.segment)
        below_segment = self.tree.get_left(segment_node)
        above_segment = self.tree.get_right(segment_node)
        self.tree.remove_by_node(segment_node)
        self.try_add_intersect(below_segment, above_segment, p.x)

