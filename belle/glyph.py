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

class OutlinedGlyphWriter(object):
    def __init__(self, char):
        self.char = char
        self.face_name = char.face
        self.char_size = char.height
        self.color = char.color
        self.outline_width = char.outline_width
        self.outline_color = char.outline_color
        
    def write(self, to, mapping=None):
        if mapping is None:
            mapping = NormalMapping
        glyph_ = self.composite(self._load_glyph(), self._load_glyph_outline())
        to.paste(glyph_, mapping(self.char.height).map(self.char, glyph_), glyph_)

    def composite(self, fill_glyph, outline_glyph):
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
            draw.bitmap((0, 0), outline_mask, self.outline_color)
        if self.char.is_filled():
            draw.bitmap((self.char.outline_width, self.char.outline_width), fill_mask, self.color)
        if self.char.rotation:
            out = out.rotate(self.char.rotation, expand=1)
        return out
        
    def _load_glyph(self):
        face = freetype.Face(self.face_name)
        face.set_char_size(int(self.char_size * 64))
        face.load_char(self.char.char, freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP)
        return face.glyph.get_glyph()

    def _load_glyph_outline(self):
        glyph = self._load_glyph()
        stroker = freetype.Stroker()
        stroker.set(int(self.outline_width * 64), freetype.FT_STROKER_LINECAP_ROUND, freetype.FT_STROKER_LINEJOIN_ROUND, 0 )
        glyph.stroke(stroker)
        return glyph

    def _write_glyph(self, glyph):
        blyph = glyph.to_bitmap(freetype.FT_RENDER_MODE_NORMAL, freetype.Vector(0,0))
        self.char.set_bitmap_offset((blyph.left, -blyph.top))
        bitmap = blyph.bitmap
        return FT2Bitmap(bitmap).to_pil_image()

    def _write_outline(self):
        return self._write_glyph(self._load_glyph_outline())

class GlyphWriter(object):
    def __init__(self, char):
        self.char = char
        self.face_name = char.face
        self.char_size = char.height
        self.color = char.color
        
    def write(self, to, mapping=None):
        if mapping is None:
            mapping = NormalMapping
        glyph = self._write_glyph()
        draw = ImageDraw.Draw(to)
        draw.bitmap(mapping(self.char.height).map(self.char, glyph), glyph, self.color)

    def _load_glyph(self):
        face = freetype.Face(self.face_name)
        face.set_char_size(int(self.char_size * 64))
        face.load_char(self.char.char, freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP)
        return face.glyph.get_glyph()

    def _write_glyph(self):
        glyph = self._load_glyph()
        blyph = glyph.to_bitmap(freetype.FT_RENDER_MODE_NORMAL, freetype.Vector(0,0))
        self.char.set_bitmap_offset((blyph.left, -blyph.top))
        bitmap = blyph.bitmap
        base = FT2Bitmap(bitmap).to_pil_image()
        if self.char.rotation:
            base = base.rotate(self.char.rotation, expand=1)
        return base

class Character(object):
    def __init__(self, char=None, x=None, y=None, width=None, height=None, rotation=None, face=None, color=None, outline_color=None, outline_width=None):
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
        self._left = None
        self._top = None

    def set_bitmap_offset(self, offset):
        self._left, self._top = offset

    def get_bitmap_offset(self):
        return (self._left, self._top)

    def is_outlined(self):
        return self.outline_color is not None

    def is_filled(self):
        return self.color is not None

class NormalMapping(object):
    def __init__(self, glyph_size):
        self.glyph_size = glyph_size

    def map(self, char, glyph):
        x, y = char.get_bitmap_offset()
        y += self.glyph_size

        x -= self.glyph_size / 2
        y -= self.glyph_size / 2
        return (char.x + x, char.y + y)

