from __future__ import print_function

import re
import struct
import sys
import freetype
import Image, ImageDraw

class Img(object):
    def __init__(self, src=None, x=None, y=None, width=None, height=None, rotation=None):
        self.src = src.filename
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = rotation

class ImgWriter(object):
    def __init__(self, img):
        self.img = img

    def write(self, to):
        im = Image.open(self.img.src).convert('RGBA')
        if self.img.width != im.size[0] or self.img.height != im.size[1]:
            im = im.resize((self.img.width, self.img.height), resample=Image.BICUBIC)
        if self.img.rotation:
            im = im.rotate(-self.img.rotation, expand=1, resample=Image.BICUBIC)

        paste_x = self.img.x - im.size[0]/2
        paste_y = self.img.y - im.size[1]/2
        to.paste(im, (paste_x, paste_y), im)

