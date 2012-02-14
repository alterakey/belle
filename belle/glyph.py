# -*- coding: utf-8 -*-
from __future__ import print_function

import logging
import math
import re
import struct
import sys
import unicodedata

import freetype
import Image, ImageDraw

log = logging.getLogger(__name__)

class FT2Bitmap(object):
    def __init__(self, bitmap):
        self.bitmap = bitmap

    def to_pil_image(self):
        data = ''.join([struct.pack('B', c) for c in self.bitmap.buffer])
        return Image.frombuffer("L", (self.bitmap.width, self.bitmap.rows), data, "raw", "L", abs(self.bitmap.pitch), 1)

class GlyphWriter(object):
    OVERRENDER_RATIO = 1.1

    def __init__(self, char):
        self.char = char
        
    def write(self, to, mapping=None):
        if mapping is None:
            if self.char.pivot == 'center':
                mapping = NormalMapping
            else:
                mapping = LeftTopMapping
        glyph_, offset = self._composite(self._load_glyph(), self._load_glyph_outline())
        coord = mapping(self.char.height).map(self.char, glyph_)
        to.paste(glyph_, (int(coord[0] + offset[0]), int(coord[1] + offset[1])), glyph_)

    def _composite(self, fill_glyph, outline_glyph):
        size = (1, 1)
        offset = (0, 0)
        if self.char.is_filled():
            fill_mask = self._write_glyph(self._load_glyph())
            size = map(max, size, fill_mask.size)
        if self.char.is_outlined():
            outline_mask = self._write_glyph(self._load_glyph_outline())
            size = map(max, size, outline_mask.size)

        out = Image.new("RGBA", [int(x * self.OVERRENDER_RATIO) for x in size], (0,0,0,0))
        draw = ImageDraw.Draw(out)

        if self.char.is_outlined():
            draw.bitmap((0, 0), outline_mask, self.char.outline_color)
        if self.char.is_filled():
            draw.bitmap((self.char.outline_width, self.char.outline_width), fill_mask, self.char.color)

        if self.char.rotation:
            theta = -self.char.rotation * math.pi / 180
            v = (out.size[0] / 2 * (1 / self.OVERRENDER_RATIO - 1), 
                 out.size[1] / 2 * (1 / self.OVERRENDER_RATIO - 1))
            offset = (v[0] * math.cos(theta) - v[1] * math.sin(theta),
                      v[0] * math.sin(theta) + v[1] * math.cos(theta))
            if self.char.rotation % 90 == 0:
                out = out.rotate(-self.char.rotation, expand=1, resample=Image.NEAREST)
            else:
                out = out.rotate(-self.char.rotation, expand=1, resample=Image.BICUBIC)
        return out, offset
        
    def _load_glyph(self):
        face = freetype.Face(self.char.face, index=self.char.index)
        face.set_char_size(int(self.char.height * 64))
        face.load_char(self.char.char, freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP)
        self.char.set_metrics(face)
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
    def __init__(self, char=None, x=None, y=None, width=None, height=None, rotation=None, face=None, color=None, outline_color=None, outline_width=None, tate=False, pivot=None, index=0):
        self.char = char
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = rotation
        self.face = face.filename
        self.index = index
        self.color = color
        self.outline_color = outline_color
        self.outline_width = outline_width
        self.tate = tate
        self.pivot = pivot
        self._left = 0
        self._top = 0
        self._width = 0
        self._height = 0
        self._metrics = None

        if not self.outline_width > 0.0:
            self.outline_width = None

        if self.policy.should_rotate:
            self.rotation += 90.0

    def set_bitmap_geom(self, geom):
        self._left, self._top, self._width, self._height = geom

    def get_bitmap_geom(self):
        return (self._left, self._top, self._width, self._height)

    def get_metrics(self):
        return self._metrics

    def set_metrics(self, face):
        metrics = face.glyph._FT_GlyphSlot.contents.metrics
        self._metrics = dict(height=metrics.height, horiBearingY=metrics.horiBearingY, ascender=face.ascender*face.size.x_scale / 65536.0, descender=face.descender*face.size.y_scale / 65536.0)

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

class LeftTopMapping(object):
    TATE_NAKA_YOKO_BASELINE_ADJ = 0.5

    def __init__(self, glyph_size):
        self.glyph_size = glyph_size

    def map(self, char, glyph):
        x, y, w, h = char.get_bitmap_geom()
        metrics = char.get_metrics()
        if not char.policy.should_transpose:
            y += self.glyph_size
        else:
            y, x = x, y

            if char.policy.should_rotate:
                if char.policy.should_realign_to_center:
                    x = -h / 2 + self.glyph_size / 2
                else:
                    gdsc = (metrics['height'] - metrics['horiBearingY']) / 64.0
                    dsc = metrics['descender'] / 64.0
                    adj = -(dsc + gdsc)
                    x = adj + dsc * self.TATE_NAKA_YOKO_BASELINE_ADJ
            else:
                x = self.glyph_size - w

        return (char.x + x, char.y + y)

class NormalMapping(object):
    def __init__(self, glyph_size):
        self.basemap = LeftTopMapping(glyph_size)

    def map(self, char, glyph):
        x, y, w, h = char.get_bitmap_geom()
        if char.policy.should_rotate:
            x, y, w, h = y, x, h, w
        return (char.x - w / 2, char.y - h / 2)

class YokogakiGlyphPolicy(object):
    def __init__(self, char):
        pass

    @property
    def should_rotate(self):
        return False

    @property
    def should_transpose(self):
        return False

    @property
    def should_realign_to_center(self):
        return False

class TategakiGlyphPolicy(object):
    always_rotate_list = u'＝ー…‥'
    always_realign_list = always_rotate_list

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

    @property
    def should_realign_to_center(self):
        if self.char in self.always_realign_list:
            return True
        if re.search(u'TILDA|DASH', self.name):
            return True
        return False
