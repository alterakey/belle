def render(asset_url, paper_width=None, paper_height=None):
    import sys
    import xml.etree.ElementTree as ET
    import Image, ImageDraw

    from belle.asset import AssetFactory
    from belle.glyph import Character, GlyphWriter, NormalMapping
    from belle.tools import HTMLColorParser, PixelCoords
    from belle.image import Img, ImgWriter

    root = ET.XML(sys.stdin.read())

    try:
        native_width = int(root.attrib['width'])
        native_height = int(root.attrib['height'])
    except KeyError:
        native_width = paper_width
        native_height = paper_height

    if paper_width is None:
        paper_width = native_width
    if paper_height is None:
        paper_height = native_height

    if (paper_width, paper_height) != (native_width, native_height):
        if native_width > native_height:
            paper_height = native_height * (paper_width / float(native_width))
        else:
            paper_width = native_width * (paper_height / float(native_height))

    im = Image.new('RGBA', (paper_width, paper_height), (255,255,255,255))
    draw = ImageDraw.Draw(im)

    for layer in root.findall('layer'):
        with AssetFactory(asset_url) as assets:
            for img_ in layer.findall('image'):
                img = Img(src=assets.get('image', img_.attrib['src']),
                          x=PixelCoords(paper_width, paper_height).u(float(img_.attrib.get('x', 0))),
                          y=PixelCoords(paper_width, paper_height).v(float(img_.attrib.get('y', 0))),
                          width=PixelCoords(paper_width, paper_height).u(float(img_.attrib.get('width', 0))),
                          height=PixelCoords(paper_width, paper_height).v(float(img_.attrib.get('height', 0))),
                          rotation=float(img_.attrib.get('rotation', 0)))
                ImgWriter(img).write(im)
                
            for char_ in layer.findall('char'):
                char = Character(char=char_.text,
                                 x=PixelCoords(paper_width, paper_height).u(float(char_.attrib.get('x', 0))),
                                 y=PixelCoords(paper_width, paper_height).v(float(char_.attrib.get('y', 0))),
                                 width=PixelCoords(paper_width, paper_height).u(float(char_.attrib.get('width', 0))),
                                 height=PixelCoords(paper_width, paper_height).v(float(char_.attrib.get('height', 0))),
                                 rotation=float(char_.attrib.get('rotation', 0)),
                                 face=assets.get('font', char_.attrib.get('face', u'')),
                                 color=HTMLColorParser(char_.attrib.get('color')).rgba(),
                                 outline_color=HTMLColorParser(char_.attrib.get('outline-color')).rgba(),
                                 outline_width=PixelCoords(paper_width, paper_height, minimum=1).u(float(char_.attrib.get('outline-edge', 0.0))),
                                 tate=(char_.attrib.get('tate') is not None))
                GlyphWriter(char).write(im, mapping=NormalMapping)
                
    im.save(sys.stdout, format="PNG")

def generate_thumbnail(asset_url, asset_id, x, y):
    from belle.asset import AssetThumbnailGenerator

    x, y = int(x), int(y)
    sys.stdout.write(AssetThumbnailGenerator(asset_url, x, y).generate(asset_id))

if __name__ == '__main__':
    import sys
    import logging
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    
    mode = sys.argv[1]
    if mode == 'render':
        render(sys.argv[2])
    elif mode == 'render-thumbnail':
        render(sys.argv[2], paper_width=int(sys.argv[3]), paper_height=int(sys.argv[4]))
    elif mode == 'generate-thumbnail':
        generate_thumbnail(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        sys.exit(127)
