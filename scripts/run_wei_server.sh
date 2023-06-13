#!/bin/bash

session="WEI"
folder="~/workspace/rpl_wei"
tmux new-session -d -s $session
tmux set -g mouse on

window=0
tmux new-window -t $session:$window -n 'redis'
tmux send-keys -t $session:$window 'cd ' $folder C-m
tmux send-keys -t $session:$window 'envsubst < redis.conf | redis-server -' C-m

window=1
tmux new-window -t $session:$window -n 'worker'
tmux send-keys -t $session:$window 'cd ' $folder C-m
tmux send-keys -t $session:$window 'source ~/wei_ws/install/setup.bash' C-m
tmux send-keys -t $session:$window 'python3 -m rpl_wei.processing.worker' C-m

window=2
tmux new-window -t $session:$window -n 'server'
tmux send-keys -t $session:$window 'cd ' $folder C-m
tmux send-keys -t $session:$window 'python3 -m rpl_wei.server --workcell ~/workspace/BIO_workcell/bio_workcell/bio_workcell.yaml' C-m

tmux attach-session -t $session

