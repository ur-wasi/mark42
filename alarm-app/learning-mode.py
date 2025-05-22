# learning_module.py sample

import json
import os

LEARNING_FILE = "learned_commands.json"

def load_learned_commands():
    if not os.path.exists(LEARNING_FILE):
        with open(LEARNING_FILE, 'w') as f:
            json.dump({}, f)
    with open(LEARNING_FILE, 'r') as f:
        return json.load(f)

def save_learned_command(phrase, action):
    data = load_learned_commands()
    data[phrase] = action
    with open(LEARNING_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_learned_action(user_input):
    data = load_learned_commands()
    return data.get(user_input)

def learn_new_command():
    print("कृपया वह वाक्य बोलें जो आप सिखाना चाहते हैं:")
    trigger = input("-> ")
    print(f"जब आप कहें '{trigger}', तब मैं क्या करूं?")
    action = input("-> (उदाहरण: play_alarm, tell_time): ")
    save_learned_command(trigger, action)
    print(f"मैंने सीख लिया है: '{trigger}' के लिए '{action}'")

# Example use in main.py:
# from learning_module import get_learned_action
# action = get_learned_action(user_input)
# if action == 'play_alarm':
#     play_alarm()
# elif action == 'tell_time':
#     tell_time()