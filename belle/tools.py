class PixelCoords(object):
    def __init__(self, width, height, minimum=None):
        self.width = width
        self.height = height
        self.minimum = minimum

    def u(self, u_):
        if u_ is not None:
            return self._clip(int(self.width * u_))
        else:
            return None

    def v(self, v_):
        if v_ is not None:
            return self._clip(int(self.height * v_))
        else:
            return None

    def _clip(self, v):
        if self.minimum:
            return max(v, self.minimum)
        else:
            return v

class HTMLColorParser(object):
    def __init__(self, color):
        self.color = color

    def rgba(self):
        m = re.match(u'#([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})', self.color)
        if not m:
            raise ValueError(u'input does not look like HTML #RRGGBB color code (%s)' % self.color)
        return (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16), 255)

