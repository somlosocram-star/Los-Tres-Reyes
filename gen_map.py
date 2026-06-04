#!/usr/bin/env python3
# Genera el mapa de "Los Tres Reyes": 42 regiones orgánicas (Voronoi + Lloyd)
# recortadas por un anillo de puntos-tampón con silueta de continente.
# Exporta JSON: {viewBox, regions:[{id, d(path SVG), cx, cy, adj:[...] }], capitals:[...]}
import numpy as np
from scipy.spatial import Voronoi
import json, math

SEED = 7
rng = np.random.default_rng(SEED)
N = 42                      # regiones jugables
CX, CY = 0.0, 0.0          # centro
R = 1.0                    # radio base del continente

# ---------- Silueta orgánica del continente (curva r(theta)) ----------
def coast_r(theta):
    # blob ligeramente alargado en vertical (móvil), con bahías suaves
    return (R
            + 0.10*math.sin(3*theta + 0.6)
            + 0.07*math.sin(5*theta + 1.7)
            + 0.05*math.sin(7*theta + 0.2)
            + 0.06*math.cos(2*theta))

# polígono fino de la costa para test punto-en-polígono
COAST = []
M = 360
for i in range(M):
    t = 2*math.pi*i/M
    r = coast_r(t)
    COAST.append((CX + r*math.cos(t)*0.86, CY + r*math.sin(t)*1.06))  # *vert un poco más alto
COAST = np.array(COAST)

def inside(p):
    x, y = p; n = len(COAST); c = False; j = n-1
    for i in range(n):
        xi, yi = COAST[i]; xj, yj = COAST[j]
        if ((yi > y) != (yj > y)) and (x < (xj-xi)*(y-yi)/(yj-yi)+xi):
            c = not c
        j = i
    return c

# ---------- Puntos-tampón: anillo orgánico que da forma a los bordes ----------
buffers = []
for i in range(64):
    t = 2*math.pi*i/64
    r = coast_r(t)*1.02
    buffers.append([CX + r*math.cos(t)*0.86, CY + r*math.sin(t)*1.06])
for i in range(40):  # segundo anillo lejano para acotar todo
    t = 2*math.pi*i/40 + 0.05
    r = 2.4
    buffers.append([CX + r*math.cos(t), CY + r*math.sin(t)])
buffers = np.array(buffers)

# ---------- Semillas interiores por rechazo ----------
pts = []
while len(pts) < N:
    x = rng.uniform(-1.2, 1.2); y = rng.uniform(-1.4, 1.4)
    if inside((x, y)):
        pts.append([x, y])
pts = np.array(pts)

def poly_centroid(poly):
    x = poly[:,0]; y = poly[:,1]
    x1 = np.roll(x,-1); y1 = np.roll(y,-1)
    cross = x*y1 - x1*y
    A = cross.sum()/2.0
    if abs(A) < 1e-12:
        return poly.mean(axis=0)
    cx = ((x+x1)*cross).sum()/(6*A)
    cy = ((y+y1)*cross).sum()/(6*A)
    return np.array([cx, cy])

# ---------- Relajación de Lloyd (8 iteraciones) ----------
for _ in range(8):
    allpts = np.vstack([pts, buffers])
    vor = Voronoi(allpts)
    newpts = pts.copy()
    for i in range(N):
        reg = vor.regions[vor.point_region[i]]
        if not reg or -1 in reg:
            continue
        poly = vor.vertices[reg]
        cen = poly_centroid(poly)
        # mantener dentro de la costa
        if inside(cen):
            newpts[i] = cen
    pts = newpts

# ---------- Voronoi final + extracción de celdas y adyacencia ----------
allpts = np.vstack([pts, buffers])
vor = Voronoi(allpts)
cells = {}
for i in range(N):
    reg = vor.regions[vor.point_region[i]]
    poly = vor.vertices[reg]
    # ordenar vértices por ángulo respecto al centroide (robustez)
    cen = poly.mean(axis=0)
    ang = np.arctan2(poly[:,1]-cen[1], poly[:,0]-cen[0])
    poly = poly[np.argsort(ang)]
    cells[i] = poly

# adyacencia a partir de ridge_points (solo entre celdas interiores)
adj = {i: set() for i in range(N)}
for (a, b) in vor.ridge_points:
    if a < N and b < N:
        adj[a].add(int(b)); adj[b].add(int(a))

# ---------- segmentos de COSTA: ridges entre una celda interior y una de tampón ----------
coast_segs = []
for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
    if v1 < 0 or v2 < 0:
        continue
    if (p1 < N) != (p2 < N):   # uno interior, otro tampón => borde de la masa terrestre
        coast_segs.append((vor.vertices[v1], vor.vertices[v2]))

# conectividad (BFS)
seen = set([0]); stack=[0]
while stack:
    u = stack.pop()
    for v in adj[u]:
        if v not in seen:
            seen.add(v); stack.append(v)
assert len(seen) == N, f"grafo no conexo: {len(seen)}/{N}"

# ---------- Escala a viewBox ----------
allv = np.vstack(list(cells.values()))
minx, miny = allv.min(axis=0); maxx, maxy = allv.max(axis=0)
PAD = 0.06*(maxx-minx)
minx-=PAD; miny-=PAD; maxx+=PAD; maxy+=PAD
W = 800.0
H = W*(maxy-miny)/(maxx-minx)
def sx(x): return (x-minx)/(maxx-minx)*W
def sy(y): return (y-miny)/(maxy-miny)*H

regions = []
cents = {}
for i in range(N):
    poly = cells[i]
    d = "M" + " L".join(f"{sx(x):.1f} {sy(y):.1f}" for x,y in poly) + " Z"
    cen = poly_centroid(poly)
    cx, cy = sx(cen[0]), sy(cen[1])
    cents[i] = (cx, cy)
    regions.append({"id": i, "d": d, "cx": round(cx,1), "cy": round(cy,1),
                    "adj": sorted(adj[i])})

# ---------- Capitales: 3 en simetría rotacional de 120° ----------
center = np.array([CX, CY])
caps = []
for k in range(3):
    ang = math.radians(90 + 120*k)
    target = center + 0.55*np.array([math.cos(ang)*0.86, math.sin(ang)*1.06])
    best, bd = None, 1e9
    for i in range(N):
        c = cells[i].mean(axis=0)
        dd = ((c-target)**2).sum()
        if dd < bd and i not in caps:
            bd = dd; best = i
    caps.append(best)
# que no sean adyacentes entre sí
for a in caps:
    for b in caps:
        if a!=b: assert b not in adj[a], "capitales adyacentes"

out = {"viewBox": f"0 0 {W:.0f} {H:.0f}", "w": round(W), "h": round(H),
       "regions": regions, "capitals": [int(c) for c in caps],
       "coast": " ".join(f"M{sx(a[0]):.1f} {sy(a[1]):.1f}L{sx(b[0]):.1f} {sy(b[1]):.1f}" for a, b in coast_segs)}
with open("/home/claude/repo/map.json","w") as f:
    json.dump(out, f, separators=(",",":"))

print(f"OK  {N} regiones | viewBox 0 0 {W:.0f} {H:.0f}")
print("capitales:", caps)
print("grados de adyacencia min/med/max:",
      min(len(a) for a in adj.values()),
      round(sum(len(a) for a in adj.values())/N,1),
      max(len(a) for a in adj.values()))
