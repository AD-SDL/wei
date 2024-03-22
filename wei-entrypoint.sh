#!/bin/bash
set -e
set -o pipefail

if [ -z "${USER_ID}" ]; then
    USER_ID=9999
fi
if [ -z "${GROUP_ID}" ]; then
    GROUP_ID=9999
fi

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


# Best-effort attempt to align permissions
chown $USER_ID:$GROUP_ID /home/app || true
chown $USER_ID:$GROUP_ID /home/app/.wei || true
chown $USER_ID:$GROUP_ID /home/app/.wei/experiments || true
chown $USER_ID:$GROUP_ID /home/app/.diaspora || true

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
