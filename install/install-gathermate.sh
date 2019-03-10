#!/bin/sh

NAME=gathermate
PREFIX="$NAME:"

PYTHON=python
eval "$PYTHON"_packages=python-minimal
GIT=git
eval "$GIT"_packages=git
PIP=pip
eval "$PIP"_packages=python-pip
REQUIRE_COMMANDS="$PYTHON $GIT"
PACKAGE_MANAGER=apt
PACKAGE_INSTALL_CMD=install
PACKAGE_UPDATE_CMD=update

REPOSITORY=https://github.com/gathermate/gathermate.git
CONFIG=config.py
REQUIRE_PYTHON=2.7

OPT=/opt
APPS=$OPT/apps
ROOT=$APPS/$NAME
VENV=$ROOT/venv
CACHE_PATH=/tmp
INSTALLED_PATH=$ROOT/install/installed.txt

init_common(){
    DAEMON_SCRIPT_PATH=$INIT_PATH/$DAEMON_SCRIPT
    SERVICE_START="$SERVICE start"
    SERVICE_STATUS="$SERVICE status"
    SERVICE_STOP="$SERVICE stop"
}

init_debian(){
    DAEMON_SCRIPT=$NAME
    REQUIREMENTS=requirements.txt
    INIT_PATH=/etc/init.d
    SERVICE="service $DAEMON_SCRIPT"
    init_common
}

init_entware(){
    REQUIRE_COMMANDS="$REQUIRE_COMMANDS $PIP"
    DAEMON_SCRIPT=S89$NAME
    PACKAGE_MANAGER=opkg
    REQUIREMENTS=requirements-entware.txt
    INIT_PATH=$OPT/etc/init.d
    CACHE_PATH=$OPT/tmp
    eval "$GIT"_packages=\"git git-http\"
    eval "$PYTHON"_packages=python-light
    SERVICE=$INIT_PATH/$DAEMON_SCRIPT
    init_common
    SERVICE_STATUS="$SERVICE check"
}

install_packages(){
    # You must decalre $packages before call it.
    echo "$PREFIX Do you want to install $packages (Y/n)"
    read -r choice
    case "$choice" in
        y|Y|"")
            echo "$PREFIX Install $packages..."
            $PACKAGE_MANAGER $PACKAGE_UPDATE_CMD
            $PACKAGE_MANAGER $PACKAGE_INSTALL_CMD $packages
            set_installed
            ;;
        n|N)
            echo "$PREFIX Exit..."
            exit 1
            ;;
        *)
            echo "$PREFIX Invalid option - exit..."
            exit 1
            ;;
    esac
}

set_installed(){
    if ! get_installed; then
        mkdir -p $(dirname $INSTALLED_PATH) && touch $INSTALLED_PATH
    fi
    list=$installed
    item=$packages
    append_to_list
    echo "$list" > $INSTALLED_PATH
}

get_installed(){
    if [ -e "$INSTALLED_PATH" ]; then
        installed=$(cat $INSTALLED_PATH)
        return 0
    else
        return 1
    fi
}

check_command(){
    # You must decalre COMMAND variable before call it.
    if [ -x "$(get_command_path)" ]; then
        return 0
    else
        echo "$PREFIX Could not execute $command."
        return 1
    fi
}

check_commands(){
    # You must decalre COMMANDS variable before call it.
    list=
    for i in $commands; do
        command=$i
        if ! check_command; then
            item=$i
            append_to_list
        fi
    done
}

get_command_path(){
    # You must decalre COMMAND variable before call it.
    echo $(which $command)
}

get_python_version(){
    echo $($PYTHON -c 'import sys; print(".".join(str(d) for d in sys.version_info[:2]))')
}

backup_file(){
    # You must declare ORIGIN variable before call it.
    local suffix="-$(date +%Y%m%d%H%M)"
    local backup=$origin$suffix
    echo "$PREFIX Backup previous $origin to $backup"
    if mv $origin $backup; then
        return 0
    else
        return 1
    fi
}

append_to_list(){
    # You must empty LIST variable before call it.
    if [ -z "$list" ]; then
        list=$item
    else
        list="$list $item"
    fi
}

check_permission(){
    echo "$PREFIX Check permission..."
    local folders="$OPT $INIT_PATH"
    list=
    for folder in $folders; do
        if [ -d "$folder" ] && [ ! -w "$folder" ]; then
            item=$folder
            append_to_list
        fi
    done
    if [ -n "$list" ]; then
        echo "$PREFIX $list is not writable."
        echo "$PREFIX Check your permission on above folder(s) first."
        echo "$PREFIX Or run script with sudo."
        echo "$PREFIX ex) sudo install-gathermate -i debian"
        exit 1
    fi
}

check_packages(){
    echo "$PREFIX Check required packages..."
    commands=$REQUIRE_COMMANDS
    check_commands
    if [ -n "$list" ]; then
        local required_commands=$list
        list=
        echo "$PREFIX It seems to be not installed : $required_commands"
        for cmd in $required_commands; do
            item=$(eval echo \$"$cmd"_packages)
            append_to_list
        done
        packages=$list
        install_packages
        check_commands
        if [ -n "$list" ]; then
            echo "$PREFIX Still could not execute $list."
            exit 1
        fi
    fi
}

before_install(){
    check_permission
    check_packages
}

after_install(){
    if [ "$target" = "entware" ]; then
        deactivate
        if ! $PYTHON -c "from lxml import etree" > /dev/null 2>&1; then
            echo "$PREFIX python-lxml is also required on $target."
            packages=python-lxml
            install_packages
        fi
        cp -r $OPT/lib/python2.7/site-packages/lxml* $VENV/lib/python2.7/site-packages
        if ! $PYTHON -c "from Crypto import Cipher" > /dev/null 2>&1; then
            echo "$PREFIX python-crypto is also required on $target."
            packages=python-crypto
            install_packages
        fi
        cp -r $OPT/lib/python2.7/site-packages/Crypto $VENV/lib/python2.7/site-packages
        if ! $PYTHON -c "import gevent" > /dev/null 2>&1; then
            echo "$PREFIX python-gevent is also required on $target."
            packages=python-gevent
        fi
        cp -r $OPT/lib/python2.7/site-packages/gevent $OPT/lib/python2.7/site-packages/greenlet.so $VENV/lib/python2.7/site-packages
    fi
    mkdir -p $ROOT/var/log $ROOT/var/run
    $SERVICE_START
}

clone_repository(){
    echo "$PREFIX Clone $REPOSITORY..."
    if [ -d "$ROOT" ]; then
        echo "$PREFIX $ROOT already exists."
        if ! $GIT clone $REPOSITORY $ROOT/tmp; then
            echo "$PREFIX Failed to clone the repository."
            exit 1
        fi
        if [ -d "$ROOT/.git" ]; then
            rm -rf $ROOT/.git
        fi
        cp -rf $ROOT/tmp/. $ROOT/
        rm -rf $ROOT/tmp
    else
        $GIT clone $REPOSITORY $ROOT
    fi

}

set_daemon_script(){
    echo "$PREFIX Check daemon script..."
    if [ -e "$DAEMON_SCRIPT_PATH" ]; then
        echo "$PREFIX $DAEMON_SCRIPT_PATH exists."
        origin=$DAEMON_SCRIPT_PATH
        if ! backup_file; then
            exit 1
        fi
    fi
    default_script="$ROOT/install/daemon-$target"
    echo "$PREFIX Copy $default_script to $DAEMON_SCRIPT_PATH"
    if cp $default_script $DAEMON_SCRIPT_PATH; then
        echo "$PREFIX Make $DAEMON_SCRIPT_PATH executable."
        chmod u=rwx,go=rx $DAEMON_SCRIPT_PATH
        sed -i -e "s@^ROOT=.*@ROOT=$APPS/\$NAME@g; s@^ACTIVATE=.*@ACTIVATE=\$ROOT/venv/bin/activate@g" $DAEMON_SCRIPT_PATH
    else
        exit 1
    fi
}

copy_config(){
    local instance_config=$ROOT/instance/$CONFIG
    if [ ! -d "$ROOT/instance" ]; then
        if ! mkdir $ROOT/instance; then
            exit 1
        fi
    fi
    if [ -e "$instance_config" ]; then
        echo "$PREFIX $instance_config exists."
        origin=$instance_config
        if ! backup_file; then
            exit 1
        fi
    fi
    echo "$PREFIX Copy $ROOT/install/user_$CONFIG to $instance_config"
    if cp $ROOT/install/user_$CONFIG $instance_config; then
        sed -i -e "s@^NAME.*@NAME = \'instance/config.py\'@g;" $instance_config
    else
        echo "$PREFIX Could not copy $ROOT/install/user_$CONFIG to $instance_config"
        exit 1
    fi
}

check_python_version(){
    echo "$PREFIX Check Python version..."
    command=$PYTHON
    local current_python=$(get_python_version)
    if [ "$current_python" = "$REQUIRE_PYTHON" ]; then
        echo "$PREFIX Python $current_python exists at $(get_command_path)"
    else
        echo "$PREFIX Python $current_python is not compatible with this program."
        packages=$(eval echo \$"$PYTHON"_packages)
        install_packages
        current_python=$(get_python_version)
        if [ "$current_python" != "$REQUIRE_PYTHON" ]; then
            echo "$PREFIX Python virsion is still $current_python"
            exit 1
        fi
    fi
    #PYTHON_ERROR=$($PYTHON -m virtualenv 2>&1 | sed -r -n -e "s/(No module).*/\1/p")
    if ! $PYTHON -c "import virtualenv" > /dev/null 2>&1; then
        if ! $PYTHON -c "import pip" > /dev/null 2>&1; then
            echo "$PREFIX Python pip module is required."
            packages=$(eval echo \$"$PIP"_packages)
            install_packages
        fi
        echo "$PREFIX Python virtualenv module is required."
        $PYTHON -m pip install virtualenv
    fi
}

make_virtualenv(){
    if [ ! -e "$VENV/bin/activate" ]; then
        echo "$PREFIX Make $PYTHON virtual environment at $VENV"
        $PYTHON -m virtualenv $VENV -p $PYTHON
        if [ ! -e "$VENV/bin/activate" ]; then
            echo "$PREFIX Could not make virtual environment."
            exit 1
        fi
    fi
}

install_python_packages(){
    . $VENV/bin/activate
    if [ ! -e $ROOT/install/$REQUIREMENTS ]; then
        echo "$PREFIX $ROOT/install/$REQUIREMENTS is not found."
        exit 1
    fi
    echo "$PREFIX Install required python packages form PyPI..."
    local install_python_requirements="$PYTHON -m $PIP install -r $ROOT/install/$REQUIREMENTS"
    if [ -d "$CACHE_PATH" ]; then
        $install_python_requirements --cache-dir $CACHE_PATH
    else
        $install_python_requirements
    fi
}

install(){
    echo "$PREFIX Install to $target"
    before_install
    clone_repository
    check_python_version
    make_virtualenv
    install_python_packages
    set_daemon_script
    copy_config
    after_install
}

uninstall(){
    echo "$PREFIX Uninstall from $target"
    check_permission
    if $SERVICE_STATUS > /dev/null 2>&1; then
        $SERVICE_STOP
    fi
    if [ -e $DAEMON_SCRIPT_PATH ]; then
        echo "$PREFIX Delete $DAEMON_SCRIPT_PATH"
        rm -f $DAEMON_SCRIPT_PATH
    fi
    get_installed
    if [ -e $ROOT ]; then
        echo "$PREFIX Delete $ROOT"
        rm -rf $ROOT
    fi
    if [ -n "$installed" ]; then
        echo "$PREFIX You can uninstall $installed manually if necessary."
        echo "$PREFIX ex) $PACKAGE_MANAGER remove $installed"
    fi
}

print_usage(){
    echo
    echo "$PREFIX This script will clone https://github.com/gathermate/gathermate.git to"
    echo "$PREFIX $ROOT folder and install packages relative to python 2.7."
    echo "$PREFIX It is made for personal use at first and only tested with"
    echo "$PREFIX Debian/Ubuntu on WSL and Entware on RT-AC68U Merlin Firmware."
    echo "$PREFIX So it has chance to not work properly."
    echo "$PREFIX You can install manually if you are not sure to run it."
    echo
    echo "$PREFIX Usage: install-gathermate.sh OPTION TARGET"
    echo
    echo "$PREFIX OPTION: -i            Install to TARGET"
    echo "$PREFIX         -u            Uninstall from TARGET"
    echo "$PREFIX TARGET: debian        Debian/Ubuntu on WSL"
    echo "$PREFIX         entware       Entware on RT-AC68U Merlin Firmware"
    echo
    echo "$PREFIX ex) install-gathermate.sh -i entware"
}

opts=$(getopt -o i:u:  -n "$NAME" -- "$@")
if [ $? != 0 ]; then
    print_usage
    exit 1
fi
eval set -- "$opts"
while true; do
    case "$1" in
        -i|--install)
            job=install
            target=$2
            shift 2
            ;;
        -u|--uninstall)
            job=uninstall
            target=$2
            shift 2
            ;;
        --)
            shift
            break
            ;;
        *)
            break
            ;;
    esac
done
if [ -z "$job" ]; then
    print_usage
    exit 0
fi
case $target in
    debian|entware)
        ;;
    *)
        echo "$PREFIX You need to choice the target. (debian or entware)"
        exit 1
        ;;
esac
echo "$PREFIX Are you sure to $job Gathermate on $target? (yes/no)"
read -r choice
case "$choice" in
    yes)
        eval init_"$target"
        $job
        ;;
    no|*)
        echo "$PREFIX Exit..."
        exit 0
        ;;
esac