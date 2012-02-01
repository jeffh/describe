#!/usr/bin/env bash

set -e

function setup () {
    if [ -z "`which pip`" ]; then
        echo "You must install pip to install requirements."
        exit 1
    fi
    if [ ! -z "$1" ]; then
        echo "Upgrading..."
        flags="--upgrade"
    fi
    pip install -r requirements.txt $flags
}

function runtests {
    nosetests
}

case "$1" in
    install)
        setup
        ;;
    upgrade)
        setup "upgrade"
        ;;
    test)
        setup
        runtests
        ;;
    *)
        echo "Usage: $0 COMMAND"
        echo
        echo "Commands: "
        echo
        echo " install - Installs the application dependencies"
        echo " test    - Installs the application and runs the tests."
        exit 1
        ;;
esac
