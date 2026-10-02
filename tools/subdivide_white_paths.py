import argparse
import sys
from collections import deque

import bpy
import bmesh


def _find_image_from_material(material: bpy.types.Material) -> bpy.types.Image | None:
    if not material or not material.use_nodes or not material.node_tree:
        return None

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    def upstream_image_from_socket(start_socket: bpy.types.NodeSocket) -> bpy.types.Image | None:
        """Walk upstream from a socket to find the first Image Texture."""
        visited_sockets: set[int] = set()
        queue: deque[bpy.types.NodeSocket] = deque([start_socket])

        while queue:
            sock = queue.popleft()
            if sock is None:
                continue
            sock_id = getattr(sock, "as_pointer", lambda: id(sock))()
            if sock_id in visited_sockets:
                continue
            visited_sockets.add(sock_id)

            if not sock.is_linked:
                continue

            for link in sock.links:
                from_sock = link.from_socket
                from_node = link.from_node

                if from_node and from_node.type == "TEX_IMAGE":
                    img = getattr(from_node, "image", None)
                    if img is not None:
                        return img

                if from_sock is not None:
                    queue.append(from_sock)

        return None

    # Prefer the image feeding the Principled BSDF Base Color (common case).
    principled_nodes = [n for n in nodes if n.type == "BSDF_PRINCIPLED"]
    for n in principled_nodes:
        base = n.inputs.get("Base Color")
        if base:
            img = upstream_image_from_socket(base)
            if img is not None:
                return img

    # Fallback: any Image Texture node in this material.
    for n in nodes:
        if n.type == "TEX_IMAGE":
            img = getattr(n, "image", None)
            if img is not None:
                return img

    return None


def _find_image_for_object(obj: bpy.types.Object) -> bpy.types.Image | None:
    if obj is None or obj.type != "MESH":
        return None

    for slot in obj.material_slots:
        mat = slot.material
        img = _find_image_from_material(mat)
        if img is not None:
            return img

    # Last resort: choose a likely image (largest, non-generated).
    candidates: list[bpy.types.Image] = []
    for img in bpy.data.images:
        if img is None:
            continue
        if img.size[0] <= 0 or img.size[1] <= 0:
            continue
        # Skip render results / viewers.
        if img.type in {"RENDER_RESULT", "COMPOSITING"}:
            continue
        candidates.append(img)

    if not candidates:
        return None

    candidates.sort(key=lambda i: (i.size[0] * i.size[1]), reverse=True)
    return candidates[0]


def _ensure_uv_layer(mesh: bpy.types.Mesh, name: str = "UVMap") -> str:
    if mesh.uv_layers:
        return mesh.uv_layers.active.name

    uv_layer = mesh.uv_layers.new(name=name)
    mesh.uv_layers.active = uv_layer

    # Best-effort unwrap: planar from view isn't available in background;
    # for a plane, "Smart UV Project" works without view context.
    obj = mesh.users_id[0] if mesh.users_id else None
    return uv_layer.name


def _sample_image_rgba(image: bpy.types.Image, u: float, v: float) -> tuple[float, float, float, float]:
    w, h = image.size
    if w <= 0 or h <= 0:
        return (0.0, 0.0, 0.0, 0.0)

    u = 0.0 if u < 0.0 else 1.0 if u > 1.0 else u
    v = 0.0 if v < 0.0 else 1.0 if v > 1.0 else v

    x = int(round(u * (w - 1)))
    y = int(round((1.0 - v) * (h - 1)))
    idx = (y * w + x) * 4

    pixels = image.pixels
    # Safety: image.pixels is a flat sequence of floats.
    if idx + 3 >= len(pixels):
        return (0.0, 0.0, 0.0, 0.0)

    return (pixels[idx], pixels[idx + 1], pixels[idx + 2], pixels[idx + 3])


def _is_white(rgba: tuple[float, float, float, float], threshold: float) -> bool:
    r, g, b, a = rgba
    # Keep it simple: require alpha > 0 and luminance high.
    if a < 0.01:
        return False
    return (r + g + b) / 3.0 >= threshold


def subdivide_mesh_faces_by_texture(
    obj: bpy.types.Object,
    image: bpy.types.Image,
    uv_layer_name: str,
    levels: int,
    cuts: int,
    white_threshold: float,
    include_center_sample: bool,
) -> tuple[int, int]:
    mesh = obj.data

    bm = bmesh.new()
    bm.from_mesh(mesh)

    uv_layer = bm.loops.layers.uv.get(uv_layer_name)
    if uv_layer is None:
        bm.free()
        raise RuntimeError(f"UV layer '{uv_layer_name}' not found on mesh")

    faces_before = len(bm.faces)

    for _ in range(levels):
        # Identify edges belonging to faces that touch white pixels.
        edges_to_subdivide: set[bmesh.types.BMEdge] = set()

        for face in bm.faces:
            hit = False

            # Sample at each corner (loop UVs).
            for loop in face.loops:
                uv = loop[uv_layer].uv
                rgba = _sample_image_rgba(image, float(uv.x), float(uv.y))
                if _is_white(rgba, white_threshold):
                    hit = True
                    break

            if not hit and include_center_sample:
                uvx = 0.0
                uvy = 0.0
                for loop in face.loops:
                    uv = loop[uv_layer].uv
                    uvx += float(uv.x)
                    uvy += float(uv.y)
                n = max(1, len(face.loops))
                uvx /= n
                uvy /= n
                rgba = _sample_image_rgba(image, uvx, uvy)
                hit = _is_white(rgba, white_threshold)

            if hit:
                for e in face.edges:
                    edges_to_subdivide.add(e)

        if not edges_to_subdivide:
            break

        bmesh.ops.subdivide_edges(
            bm,
            edges=list(edges_to_subdivide),
            cuts=cuts,
            use_grid_fill=True,
            smooth=0.0,
        )

    bm.to_mesh(mesh)
    mesh.update()

    faces_after = len(mesh.polygons)
    bm.free()

    return faces_before, faces_after


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Subdivide faces where image texture is white (via UVs).")
    parser.add_argument("--object", required=True, help="Target mesh object name")
    parser.add_argument("--levels", type=int, default=2, help="Subdivision passes in white areas")
    parser.add_argument("--cuts", type=int, default=2, help="Cuts per subdivide pass")
    parser.add_argument("--threshold", type=float, default=0.9, help="White threshold (0..1) on avg RGB")
    parser.add_argument("--include-center", action="store_true", help="Also sample face center UV")
    parser.add_argument("--out", required=True, help="Output .blend path")

    args = parser.parse_args(argv)

    obj = bpy.data.objects.get(args.object)
    if obj is None:
        raise SystemExit(f"Object '{args.object}' not found")
    if obj.type != "MESH":
        raise SystemExit(f"Object '{args.object}' is not a mesh")

    image = _find_image_for_object(obj)
    if image is None:
        raise SystemExit("Could not find an image texture used by the object")

    # Ensure image pixels are loaded.
    try:
        image.pixels[0]
    except Exception:
        image.reload()

    mesh = obj.data
    uv_name = _ensure_uv_layer(mesh)

    faces_before, faces_after = subdivide_mesh_faces_by_texture(
        obj=obj,
        image=image,
        uv_layer_name=uv_name,
        levels=max(0, args.levels),
        cuts=max(1, args.cuts),
        white_threshold=min(1.0, max(0.0, args.threshold)),
        include_center_sample=bool(args.include_center),
    )

    print(
        f"Subdivided '{obj.name}' using image '{image.name}'. Faces: {faces_before} -> {faces_after}. "
        f"(levels={args.levels}, cuts={args.cuts}, threshold={args.threshold})"
    )

    bpy.ops.wm.save_as_mainfile(filepath=args.out, compress=True)
    print(f"Saved: {args.out}")
    return 0


if __name__ == "__main__":
    # Blender passes args after '--' to the script.
    if "--" in sys.argv:
        script_args = sys.argv[sys.argv.index("--") + 1 :]
    else:
        script_args = []
    raise SystemExit(main(script_args))
