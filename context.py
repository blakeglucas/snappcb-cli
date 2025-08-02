from gerbonara import ExcellonFile, GerberFile
from shapely import Polygon, MultiPolygon
from svgwrite import Drawing

class GlobalOptions:
    def __init__(self,
                 edge_cuts_on_cu = False,
                 tool_mm = 0.125,
                 drl_dia_mm = 1,
                 cutout_dia_mm = 3,
                 mirror_bcu = True):
        self.edge_cuts_on_cu = edge_cuts_on_cu
        self.tool_mm = tool_mm
        self.drl_dia_mm = drl_dia_mm
        self.cutout_dia_mm = cutout_dia_mm
        self.mirror_bcu = mirror_bcu

class Context:
    __fcu: GerberFile | None
    __bcu: GerberFile | None
    __drl: GerberFile  | None
    __edge_cuts: GerberFile | None
    __options: GlobalOptions

    def __init__(self,
                 fcu: str | GerberFile | None,
                 bcu: str | GerberFile | None,
                 edge_cuts: str | GerberFile | None,
                 drl: str | ExcellonFile| GerberFile | None,
                 options: GlobalOptions | None = None
                 ):
        if fcu:
            self.__fcu = GerberFile.open(fcu) if type(fcu) == str else fcu
        if bcu:
            self.__bcu = GerberFile.open(bcu) if type(bcu) == str else bcu
        if edge_cuts:
            self.__edge_cuts = GerberFile.open(edge_cuts) if type(edge_cuts) == str else edge_cuts
        if drl:
            if isinstance(drl, GerberFile) or isinstance(drl, ExcellonFile):
                # FIXME apparently these are the same in this library
                self.__drl = drl
            elif type(drl) == str:
                if drl.endswith('.gbr'): # TODO more extensions? Autodetect format?
                    self.__drl = GerberFile.open(drl)
                else:
                    self.__drl = ExcellonFile.open(drl)
            else:
                # TODO throw
                pass
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
    def drl(self):
        return self.__drl
    
    @property
    def options(self):
        return self.__options
    
    @staticmethod
    def generate_svg(geom: Polygon | MultiPolygon, output_file: str):
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