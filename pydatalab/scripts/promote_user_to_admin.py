import argparse

from bson import ObjectId

from pydatalab.mongo import _get_active_mongo_client


def promote_user(display_name: str):
    matches = list(
        _get_active_mongo_client().datalabvue.users.find(
            {"display_name": display_name}, projection={"_id": 1}
        )
    )
    if len(matches) > 1:
        raise SystemExit(f"Too many matches for display name {display_name!r}")

    if len(matches) == 0:
        raise SystemExit(f"No matches for display name {display_name!r}")

    print(f"Found user: {matches[0]}")
    user_id = ObjectId(matches[0]["_id"])

    _get_active_mongo_client().datalabvue.roles.insert_one({"_id": user_id, "role": "admin"})

    print(f"Promoted {display_name} to admin.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", help="Exact display name of the user.", nargs="+")

    args = vars(parser.parse_args())

    promote_user(" ".join(args["name"]))
