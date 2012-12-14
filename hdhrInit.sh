#!/bin/sh

case "$1" in
        start)
                echo -n "Starting hdhrRec... "
                if start-stop-daemon -q -c hdhr -S -x /usr/bin/python -p /var/tmp/hdhrRec.pid -a /usr/local/bin/hdhrRec.py; then
                  echo "ok"
                else
                  echo "failed (already running?)"
                fi
                
                echo -n "Starting hdhrWeb... "
                if start-stop-daemon -q -c hdhr -S -x /usr/bin/python -p /var/tmp/hdhrWeb.pid -a /usr/local/bin/hdhrWeb.py; then
                  echo "ok"
                else
                  echo "failed (already running?)"
                fi
                ;;
                
        stop)
                echo -n "Stopping hdhrRec... "
                if start-stop-daemon -q -K -x /usr/bin/python -p /var/tmp/hdhrRec.pid; then
                  echo "ok"
                else
                  echo "failed (not running?)"
                fi
                
                echo -n "Stopping hdhrWeb... "
                if start-stop-daemon -q -K -x /usr/bin/python -p /var/tmp/hdhrWeb.pid; then
                  echo "ok"
                else
                  echo "failed (not running?)"
                fi
                ;;
        *)
                echo "Usage: $0 {start|stop}"
                exit 2
                ;;
esac
exit 0
