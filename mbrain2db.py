import glob
from util import mbrain_data2db, truncate_table

print "Truncating table"
truncate_table()

for path in glob.glob("/export/data/mmbrain/filtered/solrdocs.*.filtered"):
    print "Dealing with %s" %path
    mbrain_data2db(path)
