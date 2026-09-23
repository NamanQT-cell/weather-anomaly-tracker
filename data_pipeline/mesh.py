"""
Build an icosahedral mesh over the sphere and provide utilities to
resample lat/lon NWP grids onto mesh nodes. Using an icosphere avoids the
pole-convergence distortion you get from processing lat/lon grids as flat
2D pixel arrays -- this is the same trick used in GraphCast-style models.
"""
import numpy as np


def _normalize(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def build_icosphere(subdivisions: int = 4):
    """Return (vertices [N,3] on unit sphere, edges [E,2] node index pairs).

    subdivisions controls resolution: 4 -> ~2562 nodes, a reasonable
    demo-scale mesh. Increase for higher fidelity (costs more compute).
    """
    t = (1.0 + np.sqrt(5.0)) / 2.0
    verts = np.array([
        [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
        [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
        [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1],
    ], dtype=np.float64)
    verts = _normalize(verts)

    faces = np.array([
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ])

    for _ in range(subdivisions):
        verts, faces = _subdivide(verts, faces)

    edges = _faces_to_edges(faces)
    return verts, edges


def _subdivide(verts, faces):
    cache = {}
    new_faces = []
    verts = list(verts)

    def midpoint(i, j):
        key = tuple(sorted((i, j)))
        if key in cache:
            return cache[key]
        m = _normalize((np.array(verts[i]) + np.array(verts[j])) / 2.0)
        verts.append(m)
        idx = len(verts) - 1
        cache[key] = idx
        return idx

    for a, b, c in faces:
        ab = midpoint(a, b)
        bc = midpoint(b, c)
        ca = midpoint(c, a)
        new_faces += [[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]

    return np.array(verts), np.array(new_faces)


def _faces_to_edges(faces):
    edge_set = set()
    for a, b, c in faces:
        for i, j in ((a, b), (b, c), (c, a)):
            edge_set.add(tuple(sorted((int(i), int(j)))))
    return np.array(sorted(edge_set))


def latlon_to_xyz(lat, lon):
    lat_r, lon_r = np.radians(lat), np.radians(lon)
    x = np.cos(lat_r) * np.cos(lon_r)
    y = np.cos(lat_r) * np.sin(lon_r)
    z = np.sin(lat_r)
    return np.stack([x, y, z], axis=-1)


def xyz_to_latlon(xyz):
    x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]
    lat = np.degrees(np.arcsin(np.clip(z, -1, 1)))
    lon = np.degrees(np.arctan2(y, x))
    return lat, lon


def resample_grid_to_mesh(field, grid_lats, grid_lons, mesh_verts):
    """Nearest-neighbour resample of a lat/lon field [H,W] onto mesh nodes
    [N]. Fine for a demo; swap for area-weighted regridding (e.g. via
    `xesmf`) for production accuracy."""
    from scipy.spatial import cKDTree

    grid_xyz = latlon_to_xyz(*np.meshgrid(grid_lats, grid_lons, indexing="ij"))
    tree = cKDTree(grid_xyz.reshape(-1, 3))
    _, idx = tree.query(mesh_verts)
    return field.reshape(-1)[idx]
