# -*- coding: utf-8 -*-
import sqlalchemy as sa
import tempfile
import logging
import cStringIO
import urllib2
import re

log = logging.getLogger(__name__)

class Asset(object):
    def __init__(self, filename=None, type=None):
        self.filename = filename
        self.type = type

class AssetOperator(object):
    def match(self, key):
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
            for asset in self.content.itervalues():
                log.debug((u'removing %s' % asset.filename).encode('UTF-8'))
                os.remove(asset.filename)
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
        tmp_type = None

        if not self.conn:
            self.connect()

        for blob,type in self.operator.match(key):
            log.debug((u'extracting %s (%s) as %s' % (key, type, tmp.name)).encode('UTF-8'))
            tmp.write(blob)
            tmp_type = type

        tmp.close()
        return Asset(filename=tmp.name, type=tmp_type)

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
            return self.conn.execute(sa.sql.select([self.table.c.blob, self.table.c.type], self.table.c.hash == key))

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
        return Asset(filename=tmp.name, type=resp.info()['Content-Type'])

    @property
    def operator(self):
        return self._Operator(self.prefix)

    class _Operator(AssetOperator):
        def __init__(self, prefix):
            self.prefix = prefix

        def match(self, key):
            url = u'%s/%s' % (self.prefix, key)
            req = urllib2.Request(url)
            resp = urllib2.urlopen(req)
            try:
                return resp.read(), resp.info()['Content-Type']
            except AttributeError:
                raise resp

class ImageThumbnailer(object):
    def __init__(self, asset_blob, x, y):
        self.asset_blob = asset_blob
        self.x = x
        self.y = y

    def generate(self):
        import Image
        try:
            src = Image.open(self.asset_blob)
        except IOError:
            src = Image.new("RGBA", (self.x, self.y), (128,128,128))
        dest = cStringIO.StringIO()
        src.resize((self.x, self.y), Image.ANTIALIAS).save(dest, format="PNG")
        return dest.getvalue()

class FontThumbnailer(object):
    def __init__(self, asset_blob, x, y):
        self.asset_blob = asset_blob
        self.x = x
        self.y = y

    def generate(self):
        import Image
        face = self.asset_blob
        src = Image.new("L", (self.x, self.y), 255)

        self._typeset(src, face, u'テスト')

        dest = cStringIO.StringIO()
        src.convert("RGBA").save(dest, format="PNG")
        return dest.getvalue()

    def _typeset(self, im, face, text):
        from belle.glyph import Character, GlyphWriter, NormalMapping
        for ch in text:
            char = Character(char=ch,
                             x=0.0,
                             y=0.0,
                             width=16.0,
                             height=16.0,
                             rotation=0.0,
                             face=face,
                             color=(0,0,0))
            GlyphWriter(char).write(im, mapping=NormalMapping)


class AssetThumbnailGenerator(object):
    def __init__(self, url, x, y):
        self.url = url
        self.x = x
        self.y = y

    def generate(self, key):
        with AssetFactory(self.url) as assets:
            asset = assets.get(None, key)
            if re.search(u'^(font|ttf|ttc|otf)$', asset.type):
                return FontThumbnailer(asset.filename, self.x, self.y).generate()
            else:
                return ImageThumbnailer(asset.filename, self.x, self.y).generate()
