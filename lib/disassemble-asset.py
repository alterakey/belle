import sys
import os
import re
import sqlite3
import unicodedata

class FilePathPolicy(object):
    valid_paths = (u'fonts', u'images')

    def __init__(self, filename, type):
        self.filename = filename
        self.type = type

    def get(self):
        if self.type == 'font':
            return u'./fonts/%s' % self.filename
        if self.type == 'image':
            return u'./images/%s' % self.filename
        raise ValueError('unknown type (%s)' % self.type)

with sqlite3.connect(sys.argv[1]) as conn:
    for filename, type, blob, in conn.execute('select name, type, blob from assets'):
        for path in FilePathPolicy.valid_paths:
            try:
                os.mkdir(path)
            except OSError, e:
                if e.errno != 17:
                    raise
        path = FilePathPolicy(filename, type).get()
        print '%s' % path
        with open(path, 'wb') as f:
            f.write(blob)
            
