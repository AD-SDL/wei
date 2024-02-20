#!/bin/bash
set -e

: "${USER_ID:?USER_ID is not set}" "${GROUP_ID:?GROUP_ID is not set}"

if [ "$USER_ID" -ne 0 ] && [ "$USER_ID" -ne 9999 ]; then
    GROUP_LIST=$(groups app)
    userdel app
elif [ "$GROUP_ID" -ne 0 ] && [ "$GROUP_ID" -ne 9999 ]; then
    groupdel app
fi
if [ "$GROUP_ID" -ne 0 ] && [ "$GROUP_ID" -ne 9999 ]; then
    groupadd -g $GROUP_ID app
fi
if [ "$USER_ID" -ne 0 ] && [ "$USER_ID" -ne 9999 ]; then
    useradd -u $USER_ID --shell /bin/bash -g ${GROUP_ID} app
    usermod -aG $(echo "$GROUP_LIST" | sed 's/.*: //; s/ /,/g') app
fi


chown $USER_ID:$GROUP_ID /home/app
chown $USER_ID:$GROUP_ID /home/app/.wei
chown $USER_ID:$GROUP_ID /home/app/.diaspora

if [ "$USER_ID" -eq 0 ] && [ "$GROUP_ID" -eq 0 ]; then
    shopt -s dotglob
    for item in /home/app/*; do
        dest="/root/$(basename "$item")"

        if [ ! -e "$dest" ]; then
            ln -s "$item" "$dest"
        fi
    done
    shopt -u dotglob
    exec "$@"
else
    exec gosu app "$@"
fi
