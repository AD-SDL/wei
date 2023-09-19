#!/bin/bash

session="WEI"

folder="~/workspace/wei/wei"

window=3
tmux new-window -t $session:$window -n 'sleeper'
tmux send-keys -t $session:$window 'cd ' $folder C-m
tmux send-keys -t $session:$window 'python3 ../examples/example_clients/sleep_rest_node.py' C-m

window=4
tmux new-window -t $session:$window -n 'webcam'
tmux send-keys -t $session:$window 'cd ' $folder C-m
tmux send-keys -t $session:$window 'python3 ../examples/example_clients/webcam_rest_node.py' C-m
