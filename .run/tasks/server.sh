# vim: set ft=bash sw=3 ts=3 expandtab:

help_server() {
   echo "- run server: Run the REST server at localhost:8080"
}

task_server() {
   # using host 0.0.0.0 makes the server available on the local network
   poetry_run uvicorn sensortrack.server:API \
      --port 8080 \
      --host 0.0.0.0 \
      --app-dir src --reload \
      --log-config config/local/sensortrack/server/logging.yaml \
      --env-file config/local/sensortrack/server/server.env
}

