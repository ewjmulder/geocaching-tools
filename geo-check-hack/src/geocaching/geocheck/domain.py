import re
from dataclasses import dataclass
from enum import Enum

from geopy.distance import distance as geopy_distance
from geopy.point import Point

GEOCACHING_COORDINATE_PATTERN = re.compile(r"^([NS])(\d{1,2}) (\d{2})\.(\d{3}) *([EW])(\d{1,3}) (\d{2})\.(\d{3})$")


class Axis(Enum):
    LATITUDE = 1
    LONGITUDE = 2


class Direction(Enum):
    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"


def increase(x):
    return x + 1


def decrease(x):
    return x - 1


@dataclass
class GeocachingAngle:
    direction: Direction
    degrees: int
    minutes: int
    sub_minutes: int

    @classmethod
    def from_decimal(cls, decimal, axis: Axis):
        direction = None
        if axis == Axis.LATITUDE:
            direction = Direction.NORTH if decimal > 0 else Direction.SOUTH
        elif axis == Axis.LONGITUDE:
            direction = Direction.EAST if decimal > 0 else Direction.WEST
        decimal_abs = abs(decimal)
        degrees = int(decimal_abs)
        minutes_float = (decimal_abs - degrees) * 60
        minutes = int(minutes_float)
        sub_minutes = round((minutes_float - minutes) * 1000)
        return GeocachingAngle(direction, degrees, minutes, sub_minutes)

    def to_decimal(self):
        decimal = self.degrees + self.minutes / 60 + self.sub_minutes / 60_000
        if self.direction.value in ["S", "W"]:
            decimal *= -1
        return decimal

    def __str__(self):
        degrees_zfill = 2 if self.direction.value in ["N", "S"] else 3
        return f"{self.direction.value}{str(self.degrees).zfill(degrees_zfill)} {str(self.minutes).zfill(2)}.{str(self.sub_minutes).zfill(3)}"

    def __hash__(self):
        return hash(str(self))

    # neighbor methods will not take changing direction into account (equator, prime meridian, date line)

    # next = further north or east
    def neighbor_next(self):
        return self._add() if self.direction.value in ["N", "E"] else self._subtract()

    def _add(self):
        neighbor_degrees = self.degrees
        neighbor_minutes = self.minutes
        neighbor_sub_minutes = self.sub_minutes + 1
        if neighbor_sub_minutes == 1000:
            neighbor_sub_minutes = 0
            neighbor_minutes += 1
            if neighbor_minutes == 60:
                neighbor_minutes = 0
                neighbor_degrees += 1
        return GeocachingAngle(self.direction, neighbor_degrees, neighbor_minutes, neighbor_sub_minutes)

    # previous = further south or west
    def neighbor_previous(self):
        return self._subtract() if self.direction.value in ["N", "E"] else self._add()

    def _subtract(self):
        neighbor_degrees = self.degrees
        neighbor_minutes = self.minutes
        neighbor_sub_minutes = self.sub_minutes - 1
        if neighbor_sub_minutes == -1:
            neighbor_sub_minutes = 999
            neighbor_minutes -= 1
            if neighbor_minutes == -1:
                neighbor_minutes = 59
                neighbor_degrees -= 1
        return GeocachingAngle(self.direction, neighbor_degrees, neighbor_minutes, neighbor_sub_minutes)


@dataclass
class GeocachingPoint:
    lat_angle: GeocachingAngle
    lon_angle: GeocachingAngle

    def distance(self, other: "GeocachingPoint"):
        return geopy_distance(self.to_geopy_point(), other.to_geopy_point()).meters

    def neighbor_north(self):
        return GeocachingPoint(self.lat_angle.neighbor_next(), self.lon_angle)

    def neighbor_east(self):
        return GeocachingPoint(self.lat_angle, self.lon_angle.neighbor_next())

    def neighbor_south(self):
        return GeocachingPoint(self.lat_angle.neighbor_previous(), self.lon_angle)

    def neighbor_west(self):
        return GeocachingPoint(self.lat_angle, self.lon_angle.neighbor_previous())

    @classmethod
    def from_geopy_point(cls, point: Point):
        lat_angle = GeocachingAngle.from_decimal(point.latitude, Axis.LATITUDE)
        lon_angle = GeocachingAngle.from_decimal(point.longitude, Axis.LONGITUDE)
        return GeocachingPoint(lat_angle, lon_angle)

    def to_geopy_point(self):
        return Point(self.lat_angle.to_decimal(), self.lon_angle.to_decimal())

    @classmethod
    def from_string(cls, coordinate_string):
        match = GEOCACHING_COORDINATE_PATTERN.match(coordinate_string)
        if match is None:
            raise ValueError("Coordinate string does not match geocaching pattern")
        return GeocachingPoint(GeocachingAngle(Direction(match[1]), int(match[2]), int(match[3]), int(match[4])),
                               GeocachingAngle(Direction(match[5]), int(match[6]), int(match[7]), int(match[8])))

    def __str__(self):
        return f"{self.lat_angle} {self.lon_angle}"

    def __hash__(self):
        return hash((self.lat_angle, self.lon_angle))

    # Essentially does a 'spiral walk' around itself, collecting all points that are within the max distance.
    def sorted_point_group(self, max_distance: int):
        points_with_distance = [(self, 0)]
        steps = 1
        current = self
        at_least_one_point_within_max_distance = True
        while at_least_one_point_within_max_distance:
            at_least_one_point_within_max_distance = False
            for neighbor_method in [GeocachingPoint.neighbor_north, GeocachingPoint.neighbor_east,
                                    GeocachingPoint.neighbor_south, GeocachingPoint.neighbor_west]:
                for step in range(0, steps):
                    current = neighbor_method(current)
                    distance = current.distance(self)
                    if distance < max_distance:
                        points_with_distance.append((current, distance))
                        at_least_one_point_within_max_distance = True
                # Increase the steps after every 2 directions, to widen the spiral.
                if neighbor_method in [GeocachingPoint.neighbor_east, GeocachingPoint.neighbor_west]:
                    steps += 1
        points_with_distance.sort(key=lambda tup: tup[1])
        return [tup[0] for tup in points_with_distance]
