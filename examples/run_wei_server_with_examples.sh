#!/bin/bash

session="WEI"

folder="~/workspace/wei/wei"

tmux new-session -d -s $session
tmux set -g mouse on

window=0
tmux rename-window -t $session:$window 'redis'
tmux send-keys -t $session:$window 'cd ' $folder C-m
# Start the redis server, or ping if it's already up
if [ "$(redis-cli ping)" != "PONG" ]; then
	tmux send-keys -t $session:$window 'envsubst < $folder/../redis.conf | redis-server -' C-m
fi

window=1
tmux new-window -t $session:$window -n 'server'
tmux send-keys -t $session:$window 'cd ' $folder C-m
tmux send-keys -t $session:$window 'python3 -m wei.server --workcell ./example_workcell.yaml' C-m

window=2
tmux new-window -t $session:$window -n 'scheduler'
tmux send-keys -t $session:$window 'cd ' $folder C-m
# Uncomment the following for ROS support
# tmux send-keys -t $session:$window 'source ~/wei_ws/install/setup.bash' C-m
tmux send-keys -t $session:$window 'python3 -m wei.scheduler --workcell ./example_workcell.yaml' C-m

bash -c $folder/../examples/run_example_nodes.sh

tmux attach-session -t $session



