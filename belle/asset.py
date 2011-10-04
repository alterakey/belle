import sqlalchemy as sa
import tempfile
import logging
import cStringIO
import urllib2

log = logging.getLogger(__name__)

class AssetOperator(object):
    def match(self, key):
        pass

    def update_thumbnail(self, key, label, thumbnail):
        pass

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

        for blob, in self.operator.match(key):
            log.debug((u'extracting %s (%s) as %s' % (key, type, tmp.name)).encode('UTF-8'))
            tmp.write(blob)

        tmp.close()
        return tmp.name

    @property
    def operator(self):
        return self._Operator(self.conn)

    class _Operator(AssetOperator):
        def __init__(self, conn):
            self.conn = conn
            self.setup()

        def setup(self):
            metadata = sa.MetaData()
            metadata.reflect(bind=self.conn)
            self.table = metadata.tables['asset']

        def match(self, key):
            return self.conn.execute(sa.sql.select([self.table.c.blob], self.table.c.hash == key))

        def update_thumbnail(self, key, label, thumbnail):
            self.conn.execute(self.table.update(self.table.c.hash == key, {getattr(self.table.c, 'thumbnail_%s' % label):thumbnail}))


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

    @property
    def operator(self):
        return self._Operator(self.prefix)

    class _Operator(AssetOperator):
        def __init__(self, prefix):
            self.prefix = self.prefix

        def match(self, key):
            url = u'%s/%s' % (self.prefix, key)
            req = urllib2.Request(url)
            resp = urllib2.urlopen(req)
            try:
                return resp.read()
            except AttributeError:
                raise resp

        def update_thumbnail(self, key, label, thumbnail):
            url = u'%s/thumbnail/%s/%s' % (self.prefix, label, key)
            req = urllib2.Request(url, data=thumbnail)
            req.content_type = 'image/jpeg'
            req.get_method = lambda: 'PUT'
            resp = urllib2.urlopen(req)
            try:
                return resp.read()
            except AttributeError:
                raise resp


class AssetThumbnailGenerator(object):
    def __init__(self, url, label, x, y):
        self.url = url
        self.label = label
        self.x = x
        self.y = y

    def _update_thumbnail_for(self, assets, keys):
        import Image
        for key in keys:
            try:
                src = Image.open(assets.get('image/jpeg', key))
            except IOError:
                src = Image.new("RGB", (self.x, self.y), (128,128,128))
                dest = cStringIO.StringIO()
                src.resize((self.x, self.y), Image.ANTIALIAS).convert("RGB").save(dest, format="JPEG")
                assets.operator.update_thumbnail(key, self.label, dest.getvalue())

    def generate(self, *keys):
        with AssetFactory(self.url) as assets:
            if not isinstance(assets, SQLAAssetFactory):
                self._update_thumbnail_for(assets, keys)
            else:
                txn = assets.connect().begin()
                try:
                    self._update_thumbnail_for(assets, keys)
                    txn.commit()
                finally:
                    txn.rollback()
