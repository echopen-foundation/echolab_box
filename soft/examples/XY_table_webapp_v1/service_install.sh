#!/bin/sh
sudo cp service/echo_bench.service /lib/systemd/system/
sudo chmod 644 /lib/systemd/system/echo_bench.service
chmod +x server/bench_server.py
sudo systemctl daemon-reload
sudo systemctl enable echo_bench
sudo systemctl start echo_bench