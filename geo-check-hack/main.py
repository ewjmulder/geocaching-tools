from src.geocaching.geocheck.domain import GeocachingPoint
from src.geocaching.geocheck.hack import hack_geocheck

if __name__ == '__main__':
    # hairpin above
    center = GeocachingPoint.from_string("S41 16.814 E173 14.980")
    # hairpin below
    # center = GeocachingPoint.from_string("S41 20.362 E173 15.371")
    result = hack_geocheck("62453612c1434b2-0b65-41f5-88e2-15569960d9d4", "Verbosity", "GC6DM2N", center, 15)
    print(f"Final result: {result}")
