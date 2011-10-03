import sqlalchemy as sa
import tempfile
import logging
import cStringIO
import urllib2

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
    class FileCache(object):
        def __init__(self):
            self.content = dict()

        def __contains__(self, k):
            return k in self.content

        def __getitem__(self, k):
            return self.content[k]

        def __setitem__(self, k, v):
            self.content[k] = v

        def cleanup(self):
            import os
            for name in self.content.itervalues():
                log.debug((u'removing %s' % name).encode('UTF-8'))
                os.remove(name)
            self.content.clear()

    def __init__(self, *args, **kwargs):
        self.files = self.FileCache()

    def get(self, type, key):
        if key not in self.files:
            tmp = self.extract(type, key)
            self.files[key] = tmp
        return self.files[key]

    def cleanup(self):
        pass

    def extract(self, type, key):
        pass
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.cleanup()
        finally:
            self.files.cleanup()

class AssetFactory(object):
    def __new__(cls, url):
        if url.startswith('rest:'):
            return RestAssetFactory(url[5:])
        return SQLAAssetFactory(url)

class SQLAAssetFactory(AssetFactoryBase):
    def __init__(self, url):
        super(SQLAAssetFactory, self).__init__(url)
        self.engine = sa.create_engine(url)
        self.conn = None

    def connect(self):
        self.conn = self.engine.connect()
        return self.conn

    def cleanup(self):
        import os
        if self.conn:
            self.conn.close()
            self.conn = None

    def extract(self, type, key):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        
        if not self.conn:
            self.connect()

        for blob, in AssetOperator(self.conn).match(key):
            log.debug((u'extracting %s (%s) as %s' % (key, type, tmp.name)).encode('UTF-8'))
            tmp.write(blob)

        tmp.close()
        return tmp.name

class RestAssetFactory(AssetFactoryBase):
    def __init__(self, url):
        super(RestAssetFactory, self).__init__(url)
        self.prefix = url

    def extract(self, type, key):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        
        url = u'%s/%s' % (self.prefix, key)

        log.debug((u'requesting %s (%s) as %s [%s]' % (key, type, tmp.name, url)).encode('UTF-8'))

        req = urllib2.Request(url)
        resp = urllib2.urlopen(req)
        try:
            tmp.write(resp.read())
        except AttributeError:
            raise resp

        tmp.close()
        return tmp.name


class AssetThumbnailGenerator(object):
    def __init__(self, url, x, y):
        self.url = url
        self.x = x
        self.y = y

    def generate(self, *keys):
        import Image

        with SQLAAssetFactory(self.url) as assets:
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
