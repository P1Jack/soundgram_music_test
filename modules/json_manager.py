import json


def get_YMAPI_requester_config():
    with open('config/config.json', 'r') as read_file:
        session_id = json.load(read_file)["YMAPI"]

    return session_id


def write_json(data):
    with open('temporary/test.json', 'w') as write_file:
        json.dump(data, write_file)
