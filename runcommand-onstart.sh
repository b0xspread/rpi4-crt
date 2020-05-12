# Slightly modified from : https://github.com/Sakitoshi/retropie-crt-tvout/blob/master/to_configs/all/runcommand-onstart.sh
if [ -f "/opt/retropie/configs/$1/480i.txt" ]; then interlaced=$(tr -d "\r" < "/opt/retropie/configs/$1/480i.txt" | sed -e 's/\[/\\\[/'); fi > /dev/null
if [ -f "/opt/retropie/configs/ports/$1/480i.txt" ]; then interlaced=$(tr -d "\r" < "/opt/retropie/configs/ports/$1/480i.txt" | sed -e 's/\[/\\\[/'); fi > /dev/null
if [ ! -s "/opt/retropie/configs/$1/480i.txt" ] && [ ! -s "/opt/retropie/configs/ports/$1/480i.txt" ] || [ -z "$interlaced" ]; then interlaced="empty"; fi > /dev/null
if [ -f "/opt/retropie/configs/$1/240p.txt" ]; then progresive=$(tr -d "\r" < "/opt/retropie/configs/$1/240p.txt" | sed -e 's/\[/\\\[/'); fi > /dev/null
if [ -f "/opt/retropie/configs/ports/$1/240p.txt" ]; then progresive=$(tr -d "\r" < "/opt/retropie/configs/ports/$1/240p.txt" | sed -e 's/\[/\\\[/'); fi > /dev/null
if [ ! -s "/opt/retropie/configs/$1/240p.txt" ] && [ ! -s "/opt/retropie/configs/ports/$1/240p.txt" ] || [ -z "$progresive" ]; then progresive="empty"; fi > /dev/null
if tvservice -s | grep NTSC && { ! echo "$3" | grep -wi "$interlaced" || echo "$interlaced" | grep empty; } && ! echo "$interlaced" | grep -xi "all" && { echo "$3" | grep -wi "$progresive" || echo "$progresive" | grep empty; }; then echo 'NTSC 4:3 P' > /opt/retropie/configs/all/desired_mode/value; else echo 'NTSC 4:3 ' > /opt/retropie/configs/all/desired_mode/value;   fi
echo "runcommand-onstart $1 $2 $3"
