import redis 
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
wc_state = json.loads(r.hget("state", "wc_state"))
for module in wc_state["modules"]:
    
    