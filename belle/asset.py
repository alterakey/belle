import sqlalchemy as sa
import tempfile
import logging
import cStringIO

log = logging.getLogger(__name__)

class AssetOperator(object):
    from belle.schema import asset_table as table

    def __init__(self, conn):
        self.conn = conn

    def match(self, key):
        return self.conn.execute(sa.sql.select([self.table.c.blob], self.table.c.hash == key))

    def update_thumbnail(self, key, thumbnail):
        self.conn.execute(self.table.update(self.table.c.hash == key, {self.table.c.thumbnail:thumbnail}))

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

    def connect(self):
        self.conn = self.engine.connect()
        return self.conn

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
            self.connect()

        for blob, in AssetOperator(self.conn).match(key):
            log.debug((u'extracting %s (%s) as %s' % (key, type, tmp.name)).encode('UTF-8'))
            tmp.write(blob)

        tmp.close()
        return tmp.name

class AssetThumbnailGenerator(object):
    def __init__(self, url, x, y):
        self.url = url
        self.x = x
        self.y = y

    def generate(self, *keys):
        import Image

        with AssetFactory(self.url) as assets:
            txn = assets.connect().begin()
            try:
                for key in keys:
                    try:
                        src = Image.open(assets.get('image/jpeg', key))
                    except IOError:
                        src = Image.new("RGB", (self.x, self.y), (128,128,128))
                    dest = cStringIO.StringIO()
                    src.resize((self.x, self.y), Image.ANTIALIAS).convert("RGB").save(dest, format="JPEG")
                    AssetOperator(assets.conn).update_thumbnail(key, dest)
                txn.commit()
            finally:
                txn.rollback()
