from gerbonara import GerberFile, utils
from gerbonara.graphic_objects import GraphicObject
from gerbonara.graphic_primitives import Circle, Rectangle, Line, LengthUnit
import numpy as np
from shapely import Polygon, MultiPolygon, Point, LineString, box, unary_union, Geometry, difference
from shapely.affinity import rotate, translate, scale
from typing import Literal

from context import Context
from exceptions import DrillingException, DrillSizeException


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
            prims = obj.to_primitives(unit=utils.MM)
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
                    outline = getattr(prim, 'outline', None)
                    points = getattr(prim, 'points', None)
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
    else:
        edge_cuts_raw_geom = None
    if ctx.fcu:
        fcu_geom = trace_gerber(ctx.fcu).buffer(ctx.options.tool_mm / 2)
        if ctx.options.edge_cuts_on_cu and ctx.edge_cuts:
            fcu_geom = unary_union((fcu_geom, edge_cuts_raw_geom))
    else:
        fcu_geom = None
    if ctx.bcu:
        bcu_geom = trace_gerber(ctx.bcu).buffer(ctx.options.tool_mm / 2)
        if ctx.options.edge_cuts_on_cu and ctx.edge_cuts:
            bcu_geom = unary_union((bcu_geom, edge_cuts_raw_geom))
        if ctx.options.mirror_bcu:
            # default behavior
            bcu_geom = scale(bcu_geom, xfact=-1)
    else:
        bcu_geom = None
    if ctx.edge_cuts:
        edge_cuts_geom = _route_edge_cuts(ctx, edge_cuts_raw_geom)
    else:
        edge_cuts_geom = None
    return RoutingResult(ctx, fcu_geom, bcu_geom, edge_cuts_raw_geom, edge_cuts_geom)
    

class NccRoutingOptions:
    def __init__(self, direction: Literal['horizontal', 'vertical'] = 'horizontal'):
        self.direction = direction


def _route_ncc_layer(outer: Polygon, layer: Polygon, offset: float, options: NccRoutingOptions) -> Polygon:
    horiz = options.direction == 'horizontal'
    minx, miny, maxx, maxy = outer.bounds
    lines = []
    if horiz:
        steps = np.arange(miny - offset, maxy + offset, offset)
    else:
        steps = np.arange(minx - offset, maxx + offset, offset)
    for s in steps:
        lines.append(LineString(((minx, s), (maxx, s)) if horiz else ((s, miny), (s, maxy))).buffer(0.0000001))

    return difference(unary_union(lines), layer)
        

def ncc_routing(ctx: Context, options: NccRoutingOptions = None) -> RoutingResult:
    options = options if options else NccRoutingOptions()
    if ctx.edge_cuts:
        edge_cuts_raw_geom = trace_gerber(ctx.edge_cuts)
    else:
        edge_cuts_raw_geom = None
    if ctx.fcu:
        fcu_trace = trace_gerber(ctx.fcu)
        boundary = edge_cuts_raw_geom if ctx.edge_cuts else fcu_trace.convex_hull
        fcu_geom = _route_ncc_layer(boundary, fcu_trace, ctx.options.tool_mm / 2, options)
        if ctx.options.edge_cuts_on_cu and ctx.edge_cuts:
            fcu_geom = unary_union((fcu_geom, edge_cuts_raw_geom))
    else:
        fcu_geom = None
    if ctx.bcu:
        bcu_trace = trace_gerber(ctx.bcu)
        boundary = edge_cuts_raw_geom if ctx.edge_cuts else bcu_trace.convex_hull
        bcu_geom = _route_ncc_layer(boundary, bcu_trace, ctx.options.tool_mm / 2, options)
        if ctx.options.edge_cuts_on_cu and ctx.edge_cuts:
            bcu_geom = unary_union((bcu_geom, edge_cuts_raw_geom))
        if ctx.options.mirror_bcu:
            bcu_geom = scale(bcu_geom, xfact=-1)
    else:
        bcu_geom = None
    if ctx.edge_cuts:
        edge_cuts_geom = _route_edge_cuts(ctx, edge_cuts_raw_geom)
    else:
        edge_cuts_geom = None
    return RoutingResult(ctx, fcu_geom, bcu_geom, edge_cuts_raw_geom, edge_cuts_geom)
    

def drilling(ctx: Context) -> Polygon | MultiPolygon | None:
    if ctx.edge_cuts:
        edge_cuts_raw_geom = trace_gerber(ctx.edge_cuts)
    if ctx.drl:
        drl_geom: MultiPolygon = trace_gerber(ctx.drl)
        polys: list[Polygon] = []
        drill_min_area = np.pi * (ctx.options.drl_dia_mm / 2)**2 
        for geom in drl_geom.geoms:
            if geom.area <= drill_min_area:
                polys.append(geom.centroid.buffer(1))
            else:
                polys.append(geom.buffer(ctx.options.drl_dia_mm / -2))
        return unary_union(polys)
    return None
