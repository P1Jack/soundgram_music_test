import json


def get_session_id():
    with open('config/config.json', 'r') as read_file:
        session_id = json.load(read_file)["YMAPI"]["session_id"]

    return session_id


def write_json(data):
    with open('temporary/test.json', 'w') as write_file:
        json.dump(data, write_file)
