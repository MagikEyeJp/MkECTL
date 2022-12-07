#!/bin/bash

SCRIPT_DIR=$(cd $(dirname $0); pwd)
DESKTOP_FILE=mkectl.desktop
APP_FOLDER=~/.local/share/applications/

echo ${SCRIPT_DIR}
cp ${SCRIPT_DIR}/${DESKTOP_FILE} ${APP_FOLDER}
REPLACE_STR="s|<path to MkECTL>|"${SCRIPT_DIR}"|g"
echo ${REPLACE_STR}
sed -i -e "${REPLACE_STR}" ${APP_FOLDER}/${DESKTOP_FILE}

