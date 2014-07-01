#! /usr/bin/expect

spawn python engine.py

expect "query"
send "python\r"

expect "Please give some feedback for keywords"
#a key-value-storage database pyredis
send "database: .6\r"

expect "Please give some feedback for documents"
# 6	:python  database  pyredis  redis
# 7	:database  database  relation-database
send "6:.6,7:.4\r"

interact;
