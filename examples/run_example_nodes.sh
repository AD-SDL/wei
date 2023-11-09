#!/bin/bash

session="WEI"

folder="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )/.."

window=3
tmux new-window -t $session:$window -n 'sleeper'
tmux send-keys -t $session:$window 'cd ' $folder C-m
tmux send-keys -t $session:$window 'python3 examples/example_nodes/sleep_rest_node.py' C-m

window=4
tmux new-window -t $session:$window -n 'webcam'
tmux send-keys -t $session:$window 'cd ' $folder C-m
tmux send-keys -t $session:$window 'python3 examples/example_nodes/webcam_rest_node.py' C-m
