#!/bin/bash
set -e

if [ "$USER_ID" -ne 9999 ]; then
    GROUP_LIST=$(groups app)
    userdel app
elif [ "$GROUP_ID" -ne 9999 ]; then
    groupdel app
fi
if [ "$GROUP_ID" -ne 9999 ]; then
    groupadd -g $GROUP_ID app
fi
if [ "$USER_ID" -ne 9999 ]; then
    useradd -u $USER_ID --shell /bin/bash -g ${GROUP_ID} app
    usermod -aG $(echo "$GROUP_LIST" | sed 's/.*: //; s/ /,/g') app
fi


chown $USER_ID:$GROUP_ID /home/app/.wei
chown $USER_ID:$GROUP_ID /home/app/.diaspora

exec gosu app "$@"
