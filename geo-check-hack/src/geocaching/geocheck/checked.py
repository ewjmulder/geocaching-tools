def read_checked_points():
    file = open("checked.txt", "r")
    return file.read().splitlines()


def add_checked_point(point):
    file = open("checked.txt", "a")
    file.write(point.__str__() + "\n")
    file.close()
