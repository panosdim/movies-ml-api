#!/bin/sh
if [ "$(id -u)" != "0" ]; then
    exec sudo bash "$0" "$@"
fi

is_service_exists() {
    x="$1"
    if systemctl status "${x}" 2>/dev/null | grep -Fq "Active:"; then
        return 0
    else
        return 1
    fi
}

INSTALL_PATH=/opt/movies-ml

# Check if Python files exist in the current directory or any subdirectory
if ! find . -name "*.py" | grep -q .; then
    echo "No Python files found. Installation failed."
    exit 1
fi

# Generate a venv
python3 -m venv $INSTALL_PATH/venv
. $INSTALL_PATH/venv/bin/activate
pip install -r requirements.txt

# Check if needed files exist
if [ -f .env ] && [ -f movies-ml.service ]; then
    # Check if we upgrade or install for first time
    if is_service_exists 'movies-ml.service'; then
        systemctl stop movies-ml.service
        cp ./*.py $INSTALL_PATH
        cp ./.env $INSTALL_PATH
        systemctl start movies-ml.service
    else
        mkdir -p $INSTALL_PATH
        cp ./*.py $INSTALL_PATH
        cp ./.env $INSTALL_PATH
        cp movies-ml.service /usr/lib/systemd/system
        systemctl start movies-ml.service
        systemctl enable movies-ml.service
    fi
else
    echo "Not all needed files found. Installation failed."
    exit 1
fi
