class Document(dict):
    def __init__(self, *args, **kwargs):
        super(Document, self).__init__(*args, **kwargs)

    def __repr__(self):
        return '%d %s(%s)' %(self['id'], self['title'], ', '.join(self['keywords']))
