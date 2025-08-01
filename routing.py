from gerbonara import GerberFile
from gerbonara.graphic_objects import GraphicObject
from gerbonara.graphic_primitives import Circle, Rectangle, Line
from shapely import Polygon, Point, LineString, box, unary_union, Geometry
from shapely.affinity import rotate, translate, scale

from context import Context


class RoutingResult:
    __ctx: Context
    __fcu: Polygon | None
    __bcu: Polygon | None
    __edge_cuts_raw: Polygon | None
    __edge_cuts: Polygon | None

    def __init__(self, ctx: Context, fcu_geom: Polygon | None, bcu_geom: Polygon | None, edge_cuts_raw: Polygon | None, edge_cuts: Polygon | None):
        self.__ctx = ctx
        self.__fcu = fcu_geom
        self.__bcu = bcu_geom
        self.__edge_cuts_raw = edge_cuts_raw
        self.__edge_cuts = edge_cuts

    @property
    def context(self):
        return self.__ctx

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
    def edge_cuts_raw(self):
        return self.__edge_cuts_raw


def _init_rect(width: float, height: float) -> Polygon:
    minx = -width / 2
    miny = -height / 2
    maxx = width / 2
    maxy = height / 2
    return box(minx, miny, maxx, maxy)


def trace_gerber(gf: GerberFile):
    polys: list[Polygon] = []
    trace_segments: list[tuple] = []
    for obj in gf.objects:
        if isinstance(obj, GraphicObject):
            prims = obj.to_primitives(unit='mm')
            for prim in prims:
                if isinstance(prim, Circle):
                    polys.append(Point(prim.x, prim.y).buffer(prim.r))
                elif isinstance(prim, Rectangle):
                    rect = _init_rect(prim.w, prim.h)
                    rect = rotate(rect, prim.rotation, origin=(0, 0), use_radians=True)
                    rect = translate(rect, xoff=prim.x, yoff=prim.y)
                    polys.append(rect)
                elif isinstance(prim, Line):
                    trace_segments.append(((prim.x1, prim.y1), (prim.x2, prim.y2), prim.width))
                else:
                    outline = getattr(prim, "outline", None)
                    points = getattr(prim, "points", None)
                    if outline:
                        try:
                            polys.append(Polygon(outline))
                        except Exception:
                            pass
                    elif points:
                        polys.append(Polygon(points))
                    else:
                        # TODO warn?
                        pass

    for (p1, p2, width) in trace_segments:
        line = LineString([p1, p2])
        polys.append(line.buffer(width / 2, cap_style=1, join_style=2))

    return unary_union(polys)


def _route_edge_cuts(ctx: Context, raw_geom: Polygon = None) -> Geometry:
    base_geom = raw_geom if raw_geom else trace_gerber(ctx.edge_cuts)
    return base_geom.convex_hull.buffer(ctx.options.cutout_dia_mm / 2, join_style='round', single_sided=False)


def isolation_routing(ctx: Context) -> RoutingResult:
    if ctx.edge_cuts:
        edge_cuts_raw_geom = trace_gerber(ctx.edge_cuts)
    if ctx.fcu:
        fcu_geom = trace_gerber(ctx.fcu).buffer(ctx.options.tool_mm / 2)
        if ctx.options.edge_cuts_on_cu and ctx.edge_cuts:
            fcu_geom = unary_union((fcu_geom, edge_cuts_raw_geom))
    if ctx.bcu:
        bcu_geom = trace_gerber(ctx.bcu).buffer(ctx.options.tool_mm / 2)
        if ctx.options.edge_cuts_on_cu and ctx.edge_cuts:
            bcu_geom = unary_union((bcu_geom, edge_cuts_raw_geom))
        if ctx.options.mirror_bcu:
            # default behavior
            bcu_geom = scale(bcu_geom, xfact=-1)
    if ctx.edge_cuts:
        edge_cuts_geom = _route_edge_cuts(ctx, edge_cuts_raw_geom)
    return RoutingResult(ctx, fcu_geom, bcu_geom, edge_cuts_raw_geom, edge_cuts_geom)
    

def ncc_routing(ctx: Context):
    pass