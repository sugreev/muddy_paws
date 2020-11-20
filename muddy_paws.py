import requests
import json
import typing
import re


def is_match(dog_dict: typing.Dict):
    def _parse_age(age_string: str) -> int:
        num, _ = age_string.split()
        return 1 if num == "a" else int(num)

    def _extract_full_weight(desc: str):
        m = re.search(r"(?P<weight>\d{1,2}) ?lbs", desc)
        return int(m.group("weight")) if m else None

    current_weight = int(dog_dict["CurrentWeightPounds"])
    age = _parse_age(dog_dict["Age"])
    full_weight = _extract_full_weight(dog_dict["Description"])

    _is_match = current_weight <= 43 and full_weight <= 43 and age <= 5
    return (dog_dict["Name"], age, current_weight, full_weight, _is_match)


def make_email_content(dog_match_list: typing.List[typing.Tuple]):
    content = ""
    for dog in dog_match_list:
        content += (
            f"{dog[0]}, Age: {dog[1]}, Weights: {dog[2]},{dog[3]}, MATCH: {dog[4]}"
        )
        content += "\n"
    return content


def main():
    with open("old_ids.txt", "r") as f:
        old_ids = f.read().split(",")

    req = requests.request(
        "GET", "https://tailtracker-c8609.appspot.com/api/public/dogs"
    )
    print(f"Request Status: {req.status_code}")
    dog_list = req.json()
    available = [d for d in dog_list if d["Status"] == "Available"]
    ids = [d["ID"] for d in available]
    new_ids = set(ids).difference(old_ids)

    if new_ids:
        new_dogs = [d for d in available if d["ID"] in new_ids]
        print(
            make_email_content(
                sorted(
                    [is_match(d) for d in new_dogs], key=lambda x: x[-1], reverse=True
                )
            )
        )

        with open("old_ids.txt", "w") as f:
            f.write(",".join(ids))
    else:
        print("No updates")


if __name__ == "__main__":
    main()
