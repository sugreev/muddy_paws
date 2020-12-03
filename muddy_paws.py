import json
import typing
import re
import logging
import datetime
import os
import requests


logging.basicConfig(filename='status.log', level=logging.INFO)


def is_match(dog_dict: typing.Dict):
    """Given a dict with an adoptable dog's info,
    extract name, age, current weight, expected full grown
    weight and determine if fits criteria. Return stats and
    match decision in a tuple."""

    def _parse_age(age_string: str) -> int:
        num, _ = age_string.split()
        return 1 if num == "a" else int(num)

    def _extract_full_weight(desc: str):
        m = re.search(r"(?P<weight>\d{1,2}) ?lbs", desc)
        return int(float(m.group("weight"))) if m else None

    current_weight = int(float(dog_dict["CurrentWeightPounds"]))
    age = _parse_age(dog_dict["Age"])
    full_weight = _extract_full_weight(dog_dict["Description"])

    _is_match = current_weight <= 43 and full_weight <= 43 and age <= 5
    return (dog_dict["Name"], age, current_weight, full_weight, _is_match)


def make_log_string(dog_match_list: typing.List[typing.Tuple]):
    """Construct print-able/email-able string from
     list of match tuples"""

    content = ""
    for dog in dog_match_list:
        content += (
            f"{dog[0]}, Age: {dog[1]}, Weights: {dog[2]},{dog[3]}, MATCH: {dog[4]}"
        )
        content += "\n"
    return content


def main():
    # read last recorded list of available dog IDs
    with open("old_ids.txt", "r") as f:
        old_ids = f.read().split(",")

    # get current list of adoptable dogs
    req = requests.request(
        "GET", "https://tailtracker-c8609.appspot.com/api/public/dogs"
    )
    logging.info(f"Status: {req.status_code} at {datetime.datetime.now().isoformat()}")
    dog_list = req.json()

    # find IDs of newly available dogs
    available = [d for d in dog_list if d["Status"] == "Available"]
    ids = [d["ID"] for d in available]
    new_ids = set(ids).difference(old_ids)

    # print match decision and update ID text file
    if new_ids:
        new_dogs = [d for d in available if d["ID"] in new_ids]

        # construct email content for new dog notification
        log_lines = make_log_string(
            sorted([is_match(d) for d in new_dogs], key=lambda x: x[-1], reverse=True))
        logging.info(log_lines)

        # send email via Maker/IFTTT applet
        payload = {}
        payload["value1"] = 'NEW PUP MATCH!' if 'MATCH: True' in log_lines else 'New pups added :/'
        ifttt_key = os.environ['MAKER_KEY']
        post_url = f"https://maker.ifttt.com/trigger/muddy_paws_new_pup/with/key/{ifttt_key}"
        requests.post(url=post_url, data=payload)

        with open("old_ids.txt", "w") as f:
            f.write(",".join(ids))
    else:
        logging.info("No updates")


if __name__ == "__main__":
    main()
