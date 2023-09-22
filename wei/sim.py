import json

import redis

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
wc_state = json.loads(r.hget("state", "wc_state"))
print(wc_state)
# wc_state = {"modules": {"test": {"state": "Idle", "location": [0, 0]},"test2": {"state": "Idle", "location": [0, 20]}}}
fig, ax = plt.subplots()
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
plt.ion()
s = 0
plt.show()
while True:
    wc_state = json.loads(r.hget("state", "wc_state"))
    print(wc_state)
    s = (s + 1) % 2
    facecolor = [0, 0, 0] if s == 1 else [0.5, 0, 0.5]
    for module in wc_state["modules"]:
        if "IDLE" in str(wc_state["modules"][module]["state"]):
            facecolor = [0, 1, 0]
        elif "BUSY" in str(wc_state["modules"][module]["state"]):
            facecolor = [0, 0, 1]
        else:
            facecolor = [1, 0, 0]
        ax.add_patch(
            Rectangle(
                wc_state["modules"][module]["location"], 10, 10, facecolor=facecolor
            )
        )
    plt.pause(0.2)
