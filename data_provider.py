import json


def check_if_posted(id, username):
    data = {}
    with open('data/posted.json', 'r') as f:
        content = f.read()
        if(content == ""):
            return False
        try:
            data = json.loads(content)
        except:
            data = {}
    try:
        if id in data[username]:
            return True
        else:
            return False
    except:
        return False


def add_to_posted(id, username):
    data = {}
    with open('data/posted.json') as f:
        try:
            data = json.load(f)
        except:
            data = {}
    try:
        data[username].append(id)
    except:
        data[username] = [id]
    with open('data/posted.json', 'w') as f:
        json.dump(data, f)
