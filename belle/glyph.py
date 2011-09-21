# -*- coding: utf-8 -*-
from __future__ import print_function

import re
import struct
import sys
import freetype
import Image, ImageDraw

import logging

log = logging.getLogger(__name__)

class FT2Bitmap(object):
    def __init__(self, bitmap):
        self.bitmap = bitmap

    def to_pil_image(self):
        data = ''.join([struct.pack('B', c) for c in self.bitmap.buffer])
        return Image.frombuffer("L", (self.bitmap.width, self.bitmap.rows), data, "raw", "L", 0, 1)

class GlyphWriter(object):
    def __init__(self, char):
        self.char = char
        
    def write(self, to, mapping=None):
        if mapping is None:
            mapping = NormalMapping
        glyph_ = self._composite(self._load_glyph(), self._load_glyph_outline())
        to.paste(glyph_, mapping(self.char.height).map(self.char, glyph_), glyph_)

    def _composite(self, fill_glyph, outline_glyph):
        size = (1, 1)
        if self.char.is_filled():
            fill_mask = self._write_glyph(self._load_glyph())
            size = map(max, size, fill_mask.size)
        if self.char.is_outlined():
            outline_mask = self._write_glyph(self._load_glyph_outline())
            size = map(max, size, outline_mask.size)

        out = Image.new("RGBA", size, (0,0,0,0))
        draw = ImageDraw.Draw(out)

        if self.char.is_outlined():
            draw.bitmap((0, 0), outline_mask, self.char.outline_color)
        if self.char.is_filled():
            draw.bitmap((self.char.outline_width, self.char.outline_width), fill_mask, self.char.color)
        if self.char.rotation:
            out = out.rotate(-self.char.rotation, expand=1)
        return out
        
    def _load_glyph(self):
        face = freetype.Face(self.char.face)
        face.set_char_size(int(self.char.height * 64))
        face.load_char(self.char.char, freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP)
        return face.glyph.get_glyph()

    def _load_glyph_outline(self):
        glyph = self._load_glyph()
        stroker = freetype.Stroker()
        stroker.set(int(self.char.outline_width * 64), freetype.FT_STROKER_LINECAP_ROUND, freetype.FT_STROKER_LINEJOIN_ROUND, 0 )
        glyph.stroke(stroker)
        return glyph

    def _write_glyph(self, glyph):
        blyph = glyph.to_bitmap(freetype.FT_RENDER_MODE_NORMAL, freetype.Vector(0,0))
        self.char.set_bitmap_geom((blyph.left, -blyph.top, blyph.bitmap.width, blyph.bitmap.rows))
        bitmap = blyph.bitmap
        return FT2Bitmap(bitmap).to_pil_image()

class Character(object):
    def __init__(self, char=None, x=None, y=None, width=None, height=None, rotation=None, face=None, color=None, outline_color=None, outline_width=None, tate=False):
        self.char = char
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = rotation
        self.face = face
        self.color = color
        self.outline_color = outline_color
        self.outline_width = outline_width
        self.tate = tate
        self._left = 0
        self._top = 0
        self._width = 0
        self._height = 0

        if not self.outline_width > 0.0:
            self.outline_width = None

        if self.policy.should_rotate:
            self.rotation += 90.0

    def set_bitmap_geom(self, geom):
        self._left, self._top, self._width, self._height = geom

    def get_bitmap_geom(self):
        return (self._left, self._top, self._width, self._height)

    def is_outlined(self):
        return self.outline_color is not None and self.outline_width is not None

    def is_filled(self):
        return self.color is not None

    @property
    def policy(self):
        if self.tate:
            return TategakiGlyphPolicy(self.char)
        else:
            return YokogakiGlyphPolicy(self.char)

class NormalMapping(object):
    def __init__(self, glyph_size):
        self.glyph_size = glyph_size

    def map(self, char, glyph):
        x, y, w, h = char.get_bitmap_geom()
        if not char.policy.should_transpose:
            y += self.glyph_size
            return (char.x + x - self.glyph_size / 2, char.y + y - self.glyph_size / 2)
        else:
            if char.policy.should_rotate:
                y = -y - h
            else:
                y = self.glyph_size - w
            return (char.x + y - self.glyph_size / 2, char.y + x - self.glyph_size / 2)
            
import re
import unicodedata

class YokogakiGlyphPolicy(object):
    def __init__(self, char):
        pass

    @property
    def should_rotate(self):
        return False

    @property
    def should_transpose(self):
        return False

class TategakiGlyphPolicy(object):
    always_rotate_list = u'＝ー…‥'

    def __init__(self, char):
        self.char = char
        self.name = unicodedata.name(char)
        self.category = unicodedata.category(char)
        self.east_asian_width = unicodedata.east_asian_width(char)

    @property
    def should_rotate(self):
        if self.char in self.always_rotate_list:
            return True
        if self.east_asian_width in ('W', 'F', 'A'):
            if re.search(u'BRACKET|PARENTHESIS|TILDA|DASH', self.name):
                return True
            return False
        return True

    @property
    def should_transpose(self):
        if self.should_rotate:
            return True
        if re.search(u'(KATAK|HIRAG)ANA LETTER SMALL', self.name):
            return True
        if re.search(u'IDEOGRAPHIC', self.name):
            if self.category.startswith(u'P'):
                return True
        return False
