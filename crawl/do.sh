#! /bin/sh
#./do.sh $(limit) $(offset)
offset=$1
limit=$2

today=$(date +"%d-%m-%Y")

log_file_path="$MDATA/filtered.crawled/log/$today-offset$offset-limit$limit.log"
echo "Log file path $log_file_path";

if [ -f "$log_file_path" ]
then
    rm $log_file_path
fi

scrapy crawl -L INFO basic  -a offset=$offset -a limit=$limit --set LOG_FILE=$log_file_path
