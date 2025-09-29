#!/bin/bash
### BEGIN INIT INFO
# Provides: beryl3-preprod
# Required-Start: $local_fs $syslog
# Required-Stop:  $local_fs $syslog
# Default-Start:  2 3 4 5
# Default-Stop:   0 1 6
# Short-Description: Beryl3 Django Application Service
### END INIT INFO

# Beryl3 Production Service Script
# Manages gunicorn process for Django Europe hosting

NAME="beryl3-preprod"
PROJECT_DIR="$HOME/beryl3-preprod"
PIDFILE="$PROJECT_DIR/gunicorn.pid"
LOGFILE="$PROJECT_DIR/logs/gunicorn.log"
VENV_PATH="$HOME/.virtualenvs/beryl3-preprod"

# Gunicorn configuration
BIND="127.0.0.1:62059"
WORKERS=2
TIMEOUT=120
WORKER_CLASS="sync"

# Ensure logs directory exists
mkdir -p "$PROJECT_DIR/logs"

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
    
    echo "Starting $NAME..."
    
    # Source virtual environment and start gunicorn
    cd "$PROJECT_DIR"
    export PATH="$HOME/.local/bin:$PATH"
    source "$VENV_PATH/bin/activate"
    export DJANGO_SETTINGS_MODULE=config.settings.production
    
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
        echo "$NAME started successfully"
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
    
    echo "Stopping $NAME..."
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
    
    echo "Reloading $NAME..."
    PID=$(cat "$PIDFILE")
    kill -HUP "$PID" 2>/dev/null
    echo "$NAME reloaded"
    return 0
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
    *)
        echo "Usage: $0 {start|stop|restart|reload|status}"
        exit 1
        ;;
esac

exit $?