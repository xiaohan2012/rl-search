#! /bin/sh
#./do.sh path
path=$1
name=$(basename $path)

today=$(date +"%d-%m-%Y")

log_file_path="$MDATA/filtered.crawled/log/$today-$name.log"
echo "Log file path $log_file_path";

if [ -f "$log_file_path" ]
then
    rm $log_file_path
fi

scrapy crawl -L INFO basic  -a path=$path #--set LOG_FILE=$log_file_path
