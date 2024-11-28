import re

import requests

from src.geocaching.geocheck.domain import GeocachingPoint
from src.geocaching.geocheck.captcha import lookup_captcha
from src.geocaching.geocheck.checked import *

GEOCHECK_GUESS_PAGE = "https://geocheck.org/geo_inputchkcoord.php?gid="
GEOCHECK_CHECK_PAGE = "https://geocheck.org/geo_chkcoord.php"


def hack_geocheck(geocheck_id: str, cache_name: str, gc_code: str, center: GeocachingPoint, max_distance: int):
    points = center.sorted_point_group(max_distance)
    # point_groups = in_groups_of(points, 10)
    # for point_group in point_groups:
    #     connect_to_vpn()
    for point in points:
        if make_guess(geocheck_id, cache_name, gc_code, point):
            return point.__str__()
        add_checked_point(point)
    return "Not found"


def connect_to_vpn():
    print("TODO: connect to VPN")
    input("Press Enter to continue...")
    pass


def make_guess(geocheck_id: str, cache_name: str, gc_code: str, point: GeocachingPoint):
    if point.__str__() in read_checked_points():
        print("Point already checked, skipping...")
        return False

    attempts_left = False
    while not attempts_left:
        session = requests.session()
        guess_page_text = get_guess_page(session, geocheck_id)
        if "You have exceeded the limit of 10 attempts in 10 minutes" in guess_page_text:
            print("Used all the attempts on this server")
            connect_to_vpn()
        else:
            attempts_left = True

    captcha_hash = re.search(r"validateChkCoordsForm\(this,'([0-9a-z]+)'\)", guess_page_text).group(1)
    captcha = lookup_captcha(captcha_hash)

    payload = {
        "gid": geocheck_id,
        "cachename": cache_name,
        "gccode": gc_code,
        "coordOneField": point.__str__().replace(".", "").replace(" ", ""),
        "usercaptcha": captcha
    }

    check_page = session.post(GEOCHECK_CHECK_PAGE, data=payload)
    if "your solution is correct" in check_page.text:
        print(f"Solution found! {point.__str__()}")
        return True
    else:
        print(f"Solution incorrect! {point.__str__()}")
        return False


def get_guess_page(session, geocheck_id):
    guess_url = GEOCHECK_GUESS_PAGE + str(geocheck_id)
    guess_page_result = session.get(url=guess_url)
    if guess_page_result.status_code != 200:
        raise Exception(f"Error with guess page: {guess_page_result.status_code} - {guess_page_result.text}")

    return guess_page_result.text
