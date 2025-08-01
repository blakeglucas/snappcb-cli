from gerbonara import GerberFile
from shapely import Polygon
from svgwrite import Drawing
from typing import Union

class GlobalOptions:
    def __init__(self,
                 edge_cuts_on_cu = False,
                 annotations_on_cu = False,
                 tool_mm = 0.125,
                 drl_dia_mm = 0,
                 cutout_dia_mm = 3,
                 tabs = False,
                 mirror_bcu = True):
        self.edge_cuts_on_cu = edge_cuts_on_cu
        self.annotations_on_cu = annotations_on_cu
        self.tool_mm = tool_mm
        self.drl_dia_mm = drl_dia_mm
        self.cutout_dia_mm = cutout_dia_mm
        self.tabs = tabs
        self.mirror_bcu = mirror_bcu

class Context:
    __fcu: Union[GerberFile | None]
    __bcu: Union[GerberFile | None]
    __drl: None
    __edge_cuts: Union[GerberFile | None]
    __options: GlobalOptions

    def __init__(self,
                 fcu: str | GerberFile | None,
                 bcu: str | GerberFile | None,
                 edge_cuts: str | GerberFile | None,
                 options: GlobalOptions | None = None
                 ):
        if fcu:
            self.__fcu = GerberFile.open(fcu) if type(fcu) == str else fcu
        if bcu:
            self.__bcu = GerberFile.open(bcu) if type(bcu) == str else bcu
        if edge_cuts:
            self.__edge_cuts = GerberFile.open(edge_cuts) if type(edge_cuts) == str else edge_cuts
        self.__options = GlobalOptions() if options is None else options

    @property
    def fcu(self):
        return self.__fcu
    
    @property
    def bcu(self):
        return self.__bcu
    
    @property
    def edge_cuts(self):
        return self.__edge_cuts
    
    @property
    def options(self):
        return self.__options
    
    @staticmethod
    def generate_svg(geom: Polygon, output_file: str):
        minx, miny, maxx, maxy = geom.bounds
        w = maxx - minx
        h = maxy - miny
        dwg = Drawing(output_file, size=(f'{w}mm', f'{h}mm'), profile='tiny', viewBox=f'0 0 {w} {h}')

        def draw(poly: Polygon):
            paths = [poly.exterior.coords] + [i.coords for i in poly.interiors]
            for path in paths:
                pts = [(x - minx, maxy - y) for x, y in path]
                dwg.add(dwg.polyline(pts, fill='none', stroke = 'black', stroke_width = 0.1))

        if geom.geom_type == 'Polygon':
            draw(geom)
        else:
            for p in geom.geoms:
                draw(p)

        dwg.save()
        print("Saved SVG:", output_file)