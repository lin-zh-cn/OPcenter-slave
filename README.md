(nohup python3 /wwwroot/OPcenter-slave/slave-start.py > /dev/null 2 > /wwwroot/OPcenter-slave/runlog &) & echo $! > /wwwroot/OPcenter-slave/pidfile.pid
