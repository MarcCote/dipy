from __future__ import division

import numpy as np
from itertools import izip

from dipy.viz import actor, window

from dipy.tracking.streamline import get_bounding_box_streamlines
from dipy.viz import fvtk
from dipy.viz.fvtk import colors
from dipy.viz.colormap import distinguishable_colormap


def show_bundles(bundles, colormap=None):
    bg = (0, 0, 0)
    if colormap is None:
        colormap = distinguishable_colormap(bg=bg)

    ren = window.Renderer()
    ren.background(bg)
    #ren.projection("parallel")

    for bundle, color in zip(bundles, colormap):
        stream_actor = actor.line(bundle, [color]*len(bundle), linewidth=1)
        ren.add(stream_actor)

    #ren.reset_camera_tight()
    show_m = window.ShowManager(ren, interactor_style="trackball")
    show_m.start()


def show_clusters(bundles, bg=(1, 1, 1), show=False):
    ren = window.Renderer()
    ren.background(bg)
    #ren.projection("parallel")

    for cluster in bundles:
        stream_actor = actor.line(cluster, [cluster.color]*len(cluster), linewidth=2)
        ren.add(stream_actor)

    if show:
        window.show(ren)

    return ren


def show_hierarchical_clusters(tree, theta_range=(0, np.pi), show_circles=False, size=(900, 900)):
    bg = (1, 1, 1)
    #ren = fvtk.ren()
    #fvtk.clear(ren)
    #ren.SetBackground(*bg)

    renderer = window.Renderer()
    renderer.background(bg)

    box_min, box_max = get_bounding_box_streamlines(tree.root)
    width, height, depth = box_max - box_min
    box_size = max(width, height, depth)

    thresholds = set()
    max_threshold = tree.root.threshold
    box_size *= len(tree.root.children) * (theta_range[1]-theta_range[0]) / (2*np.pi)

    def _draw_subtree(node, color=colors.orange_red, theta_range=theta_range, parent_pos=(0, 0, 0)):
        print np.array(theta_range) / np.pi * 360

        # Draw node
        offset = np.zeros(3)
        theta = theta_range[0] + (theta_range[1] - theta_range[0]) / 2.

        radius = max_threshold - node.threshold
        thresholds.add(node.threshold)

        offset[0] += radius*box_size * np.cos(theta)
        offset[1] -= radius*box_size * np.sin(theta)
        #fvtk.add(ren, fvtk.line([s + offset for s in node], [color]*len(node), linewidth=2))
        #fvtk.add(ren, fvtk.line(np.array([parent_pos, offset]), fvtk.colors.black, linewidth=1))
        renderer.add(actor.line([s + offset for s in node], [color]*len(node), linewidth=2))
        renderer.add(actor.line(np.array([parent_pos, offset]), colors.black, linewidth=1))

        if len(node.children) == 0:
            return

        children = sorted(node.children, key=lambda c: len(c))
        ratios = np.maximum([len(c) / len(node) for c in children], 0.1)
        ratios = ratios / np.sum(ratios)  # Renormalize
        sections = theta_range[0] + np.cumsum([0] + ratios.tolist()) * (theta_range[1] - theta_range[0])

        colormap = distinguishable_colormap(bg=bg)
        for i, (node, color) in enumerate(izip(children, colormap)):
            _draw_subtree(node, color, (sections[i], sections[i+1]), offset)

    _draw_subtree(tree.root)

    # Draw circles for the different radius
    if show_circles:
        for threshold in sorted(thresholds)[:-1]:
            print threshold
            radius = max_threshold - threshold
            theta = -np.linspace(*theta_range, num=200)
            X = radius*box_size * np.cos(theta)
            Y = radius*box_size * np.sin(theta)
            Z = np.zeros_like(X)
            dashed_line = zip(np.array([X, Y, Z]).T[::4], np.array([X, Y, Z]).T[1::4])
            #fvtk.add(ren, fvtk.line(dashed_line, fvtk.colors.black, linewidth=1))
            renderer.add(actor.line(dashed_line, colors.black, linewidth=1))

            scale = box_size/8.
            text = "{:.1f}mm".format(threshold)
            pos = np.array([X[0], Y[0], Z[0]]) + np.array([-len(text)/2.*scale, scale/2., 0])
            #fvtk.label(ren, text=text, pos=pos, scale=scale, color=(0, 0, 0))

            pos = np.array([X[-1], Y[-1], Z[-1]]) + np.array([-len(text)/2.*scale, scale/2., 0])
            #fvtk.label(ren, text=text, pos=pos, scale=scale, color=(0, 0, 0))

    #fvtk.show(ren, size=size)
    window.show(renderer)
    #return fvtk


def show_clusters_graph_progress(tree, max_indices, bg=(1, 1, 1), show=False):
    import networkx as nx

    scaling = 4
    for max_index in max_indices:
        G = nx.Graph()
        cpt = [0]

        def _tag_node(node):
            if np.sum(node.indices < max_index) == 0:
                return

            node.id = cpt[0]
            cpt[0] += 1

            indices = np.argsort(map(len, node.children))[::-1]
            for idx in indices:
                child = node.children[idx]
                # if len(child) < 10:
                #     continue
                _tag_node(child)

        _tag_node(tree.root)

        def _build_graph(node):
            if np.sum(node.indices < max_index) == 0:
                return

            for child in node.children:
                # if len(child) < 10:
                #     continue
                #G.add_edge(node, child)
                G.add_edge(node.id, child.id)
                _build_graph(child)

        _build_graph(tree.root)
        positions = nx.graphviz_layout(G, prog='twopi', args='')

        lines = [[]]
        renderer = window.Renderer()
        renderer.background(bg)

        def _draw_subtree(node):
            if np.sum(node.indices < max_index) == 0:
                return

            global colormap
            # Draw node
            node_pos = np.hstack([positions[node.id], 0]) * scaling

            if node.color is not None:
                mean = np.mean([np.mean(s, axis=0) for s in node], axis=0)
                streamlines = [s - mean + node_pos for s, i in zip(node, node.indices) if i < max_index]
                if len(streamlines) > 0:
                    stream_actor = actor.line(streamlines, [node.color]*len(node), linewidth=2)
                    renderer.add(stream_actor)

            if node.parent is not None:
                parent_pos = np.hstack([positions[node.parent.id], 0]) * scaling
                lines[0].append(np.array([parent_pos, node_pos]))

            for child in node.children:
                _draw_subtree(child)

        _draw_subtree(tree.root)

        renderer.add(actor.line(lines[0], colors.black, linewidth=1))

        if show:
            window.show(renderer)

        yield renderer


def show_clusters_graph(tree, bg=(1, 1, 1), show=False, show_id=False):
    import networkx as nx

    renderer = window.Renderer()
    renderer.background(bg)

    G = nx.Graph()
    cpt = [0]

    def _tag_node(node):
        node.id = cpt[0]
        cpt[0] += 1

        indices = np.argsort(map(len, node.children))[::-1]
        for idx in indices:
            child = node.children[idx]
            # if len(child) < 10:
            #     continue
            _tag_node(child)

    _tag_node(tree.root)

    def _build_graph(node):
        for child in node.children:
            # if len(child) < 10:
            #     continue
            #G.add_edge(node, child)
            G.add_edge(node.id, child.id)
            _build_graph(child)

    _build_graph(tree.root)
    positions = nx.graphviz_layout(G, prog='twopi', args='')
    #positions = hierarchy_pos(G, 0)

    # def _add_siblings(node):
    #     for i in range(1, len(node.children)):
    #         G.add_edge(node.children[i-1].id, node.children[i].id)
    #         _add_siblings(node.children[i])

    # _add_siblings(tree.root)

    # positions = nx.spring_layout(G, scale=1000, pos=positions)
    #positions = nx.spring_layout(G, scale=1000)

    scaling = 4
    lines = [[]]

    def _draw_subtree(node):
        global colormap
        # Draw node
        node_pos = np.hstack([positions[node.id], 0]) * scaling

        if node.color is not None:
            mean = np.mean([np.mean(s, axis=0) for s in node], axis=0)
            #stream_actor = actor.line([s - mean + node_pos for s in node], [node.color]*len(node), linewidth=2)
            stream_actor = actor.streamtube([s - mean + node_pos for s in node], [node.color]*len(node), linewidth=1)
            #stream_actor = auto_orient(stream_actor, direction=(-1, 0, 0), bbox_type="AABB")
            #stream_actor.SetPosition(node_pos - stream_actor.GetCenter())
            renderer.add(stream_actor)

        if node.parent is not None:
            parent_pos = np.hstack([positions[node.parent.id], 0]) * scaling
            lines[0].append(np.array([parent_pos, node_pos]))

            if show_id:
                #fvtk.label(renderer, text=str(node.id), pos=node_pos+np.array([10, 10, 0]), scale=50, color=(0, 0, 0))
                renderer.add(actor.text_3d(text=str(node.id),
                                           position=node_pos+(parent_pos-node_pos)/2.,
                                           color=(0, 0, 0)))

        for child in node.children:
            _draw_subtree(child)

    _draw_subtree(tree.root)

    #renderer.add(actor.line(lines[0], colors.black, linewidth=1))
    renderer.add(actor.streamtube(lines[0], colors.grey, linewidth=1, opacity=0.6))

    if show:
        window.show(renderer)

    return renderer


def hierarchy_pos(G, root, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5 ):
    '''If there is a cycle that is reachable from root, then result will not be a hierarchy.

       G: the graph
       root: the root node of current branch
       width: horizontal space allocated for this branch - avoids overlap with other branches
       vert_gap: gap between levels of hierarchy
       vert_loc: vertical location of root
       xcenter: horizontal location of root
    '''

    def h_recur(G, root, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5,
                  pos = None, parent = None, parsed = [] ):
        if(root not in parsed):
            parsed.append(root)
            if pos == None:
                pos = {root:(xcenter,vert_loc)}
            else:
                pos[root] = (xcenter, vert_loc)
            neighbors = G.neighbors(root)
            if parent != None:
                neighbors.remove(parent)
            if len(neighbors)!=0:
                dx = width/len(neighbors)
                nextx = xcenter - width/2 - dx/2
                for neighbor in neighbors:
                    nextx += dx
                    pos = h_recur(G,neighbor, width = dx, vert_gap = vert_gap,
                                        vert_loc = vert_loc-vert_gap, xcenter=nextx, pos=pos,
                                        parent = root, parsed = parsed)
        return pos

    return h_recur(G, root, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5)



def show_clusters_tree_path(tree, path, bg=(1, 1, 1), show=False, show_id=False):
    import networkx as nx

    renderer = window.Renderer()
    renderer.background(bg)

    G = nx.Graph()
    cpt = [0]

    def _tag_node(node):
        node.id = cpt[0]
        cpt[0] += 1

        indices = np.argsort(map(len, node.children))[::-1]
        for idx in indices:
            child = node.children[idx]
            # if len(child) < 10:
            #     continue
            _tag_node(child)

    _tag_node(tree.root)

    def _build_graph(node, level=0):
        for child in node.children:
            # if len(child) < 10:
            #     continue
            #G.add_edge(node, child)

            if child.id in path[level] or len(path[level]) == 0:
                G.add_edge(node.id, child.id, constraint=False)
                _build_graph(child, level+1)

    _build_graph(tree.root)
    positions = hierarchy_pos(G, 0)

    scaling = 1500
    lines = [[]]

    global colormap
    colormap = iter(distinguishable_colormap(bg=bg))

    def _draw_subtree(node):
        global colormap
        if node.id not in positions:
            return

        # Draw node
        node_pos = np.hstack([positions[node.id], 0]) * scaling

        if node.color is not None:
            mean = np.mean([np.mean(s, axis=0) for s in node], axis=0)
            #color = next(colormap)
            color = node.color
            #stream_actor = actor.line([s - mean + node_pos for s in node], [color]*len(node), linewidth=6)
            stream_actor = actor.streamtube([s - mean + node_pos for s in node], [color]*len(node), linewidth=1)
            renderer.add(stream_actor)

        if node.parent is not None:
            parent_pos = np.hstack([positions[node.parent.id], 0]) * scaling
            lines[0].append(np.array([parent_pos, node_pos]))

        for child in node.children:
            _draw_subtree(child)

    _draw_subtree(tree.root)

    #renderer.add(actor.line(lines[0], colors.grey, linewidth=3, opacity=0.6))
    renderer.add(actor.streamtube(lines[0], colors.grey, linewidth=0.5, opacity=1))

    if show:
        window.show(renderer)

    return renderer
