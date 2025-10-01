#!/bin/bash
### BEGIN INIT INFO
# Provides: beryl3
# Required-Start: $local_fs $syslog
# Required-Stop:  $local_fs $syslog
# Default-Start:  2 3 4 5
# Default-Stop:   0 1 6
# Short-Description: Beryl3 Django Application Service
### END INIT INFO

# Beryl3 Service Script - Auto-detects preprod vs production environment
# Manages gunicorn process for Django Europe hosting

# Auto-detect environment based on current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(basename "$SCRIPT_DIR")"

if [[ "$BASE_DIR" == "beryl3-preprod" ]]; then
    ENV="preprod"
    NAME="beryl3-preprod"
    PROJECT_DIR="$HOME/beryl3-preprod"
    VENV_PATH="$HOME/.virtualenvs/beryl3-preprod"
    BIND="127.0.0.1:62059"
    SETTINGS_MODULE="config.settings.production"
elif [[ "$BASE_DIR" == "beryl3" ]]; then
    ENV="production"
    NAME="beryl3-production"
    PROJECT_DIR="$HOME/beryl3"
    VENV_PATH="$HOME/.virtualenvs/beryl3"
    BIND="127.0.0.1:62079"
    SETTINGS_MODULE="production_settings"
else
    echo "Error: Unknown environment. Script must be run from beryl3-preprod or beryl3 directory."
    exit 1
fi

PIDFILE="$PROJECT_DIR/gunicorn.pid"
LOGFILE="$PROJECT_DIR/logs/gunicorn.log"

# Gunicorn configuration
WORKERS=2
TIMEOUT=120
WORKER_CLASS="sync"

# Ensure logs directory exists
mkdir -p "$PROJECT_DIR/logs"

echo "Beryl3 Service Manager - Environment: $ENV"

status() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "$NAME is running (PID: $PID)"
            return 0
        else
            echo "$NAME is not running (stale PID file)"
            rm -f "$PIDFILE"
            return 1
        fi
    else
        echo "$NAME is not running"
        return 1
    fi
}

start() {
    if status > /dev/null; then
        echo "$NAME is already running"
        return 1
    fi
    
    echo "Starting $NAME ($ENV environment)..."
    
    # Source virtual environment and start gunicorn
    cd "$PROJECT_DIR"
    export PATH="$HOME/.local/bin:$PATH"
    source "$VENV_PATH/bin/activate"
    export DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE"
    
    gunicorn config.wsgi:application \
        --bind "$BIND" \
        --workers "$WORKERS" \
        --timeout "$TIMEOUT" \
        --worker-class "$WORKER_CLASS" \
        --pid "$PIDFILE" \
        --daemon \
        --access-logfile "$PROJECT_DIR/logs/access.log" \
        --error-logfile "$PROJECT_DIR/logs/error.log" \
        --log-level info
    
    # Wait a moment and check if it started
    sleep 2
    if status > /dev/null; then
        echo "$NAME started successfully on $BIND"
        return 0
    else
        echo "Failed to start $NAME"
        return 1
    fi
}

stop() {
    if ! status > /dev/null; then
        echo "$NAME is not running"
        return 0
    fi
    
    echo "Stopping $NAME ($ENV environment)..."
    PID=$(cat "$PIDFILE")
    
    # Send QUIT signal to gracefully stop gunicorn
    kill -QUIT "$PID" 2>/dev/null
    
    # Wait for process to stop
    for i in {1..30}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            rm -f "$PIDFILE"
            echo "$NAME stopped"
            return 0
        fi
        sleep 1
    done
    
    # If still running, force kill
    echo "Force killing $NAME..."
    kill -KILL "$PID" 2>/dev/null
    rm -f "$PIDFILE"
    echo "$NAME stopped (forced)"
    return 0
}

restart() {
    stop
    sleep 2
    start
}

reload() {
    if ! status > /dev/null; then
        echo "$NAME is not running"
        return 1
    fi
    
    echo "Reloading $NAME ($ENV environment)..."
    PID=$(cat "$PIDFILE")
    kill -HUP "$PID" 2>/dev/null
    echo "$NAME reloaded"
    return 0
}

info() {
    echo "Beryl3 Service Configuration:"
    echo "  Environment: $ENV"
    echo "  Name: $NAME"
    echo "  Project Dir: $PROJECT_DIR"
    echo "  Virtual Env: $VENV_PATH"
    echo "  Bind Address: $BIND"
    echo "  Settings Module: $SETTINGS_MODULE"
    echo "  PID File: $PIDFILE"
    echo "  Log Directory: $PROJECT_DIR/logs"
    echo ""
    status
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    reload)
        reload
        ;;
    status)
        status
        ;;
    info)
        info
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|reload|status|info}"
        echo ""
        echo "This script auto-detects the environment based on the directory:"
        echo "  beryl3-preprod/ -> preprod environment (port 62059)"
        echo "  beryl3/         -> production environment (port 62079)"
        exit 1
        ;;
esac

exit $?