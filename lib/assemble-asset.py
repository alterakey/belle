import sys
import os
import re
import sqlite3
import unicodedata

class FileTypeGuesser(object):
    def __init__(self, filename):
        self.filename = filename

    def guess(self):
        if re.search('(otf|ttf|ttc|fon)$', filename):
            return 'font'
        if re.search('(bmp|png|gif|jpg)$', filename):
            return 'image'
        return 'unknown'

with sqlite3.connect('./assets.db') as conn:
    conn.execute(u'create table if not exists assets (name varchar unique, type varchar, blob blob)')

    for filename in sys.argv[1:]:
        filename = unicodedata.normalize('NFC', unicode(filename, 'UTF-8'))
        with open(filename, 'rb') as f:
            print filename, os.path.getsize(filename)
            conn.execute(u'insert into assets (name,type,blob) values (?,?,?)', (os.path.basename(filename), FileTypeGuesser(filename).guess(), buffer(f.read())))
            conn.commit()

