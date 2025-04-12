from typing import List, Tuple

import structlog

from .coords import detect_crs_from_cxf, transform_cxf_vertices

logger = structlog.get_logger("catasto.carto")


def transform_vertices(vertices: List[Tuple], mun_code: str) -> List[Tuple]:
    crs = detect_crs_from_cxf(vertices=vertices, mun_code=mun_code)
    if crs == "cassini-soldner":
        t_vertices = transform_cxf_vertices(
            vertices=vertices,
            source_crs="cassini-soldner",
            target_crs="gauss-boaga-east",
            mun_code=mun_code,
        )
        out_vertices = t_vertices
    elif crs == "gauss-boaga-west":
        t_vertices = transform_cxf_vertices(
            vertices=vertices,
            source_crs="gauss-boaga-west",
            target_crs="gauss-boaga-east",
            mun_code=mun_code,
        )
        out_vertices = t_vertices
    elif crs == "gauss-boaga-east":
        logger.info("Skip coordinates transformation")
        pass

    return out_vertices
