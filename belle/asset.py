import sqlalchemy as sa
import tempfile
import logging

log = logging.getLogger(__name__)

class AssetFactoryBase(object):
    def cleanup(self):
        pass
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

class AssetFactory(AssetFactoryBase):
    def __init__(self, url):
        self.engine = sa.create_engine(url)
        self.conn = None
        self.blobs = dict()

    def get(self, type, key):
        if key not in self.blobs:
            tmp = self._extract(type, key)
            self.blobs[key] = tmp
        return self.blobs[key]

    def cleanup(self):
        import os
        if self.conn:
            self.conn.close()
            self.conn = None
        for name in self.blobs.itervalues():
            log.debug((u'removing %s' % name).encode('UTF-8'))
            os.remove(name)
        self.blobs = dict()

    def _extract(self, type, key):
        tmp = tempfile.NamedTemporaryFile(delete=False)

        if not self.conn:
            self.conn = self.engine.connect()

        for blob, in self.conn.execute('select blob from assets where type=? and name=?', (type, key)):
            log.debug((u'extracting %s (%s) as %s' % (key, type, tmp.name)).encode('UTF-8'))
            tmp.write(blob)

        tmp.close()
        return tmp.name
