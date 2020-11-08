for KILLPID in `ps ax | grep ‘http_server’ | awk ‘{print $1;}’`; do
kill -9 $KILLPID;
done
