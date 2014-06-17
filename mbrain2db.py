import glob
from util import mbrain_data2db, update_by_url


def insert():
    #print "Truncating table"
    #truncate_table()

    for path in glob.glob("/export/data/mmbrain/filtered/solrdocs.*.filtered"):
        print "Dealing with %s" %path
        mbrain_data2db(path, table = "webpage")

def update():
    for path in glob.glob("/export/data/mmbrain/filtered/solrdocs.*.filtered"):
        update_by_url(path, 
                      fields = ["publishDate"])

if __name__ == "__main__":
    update()
