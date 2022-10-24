# vim: set ft=bash sw=3 ts=3 expandtab:
# runscript: customized=true

help_database() {
   echo "- run database: Run the InfluxDB & Grafana servers via docker-compose"
}

task_database() {
   docker-compose up
}

