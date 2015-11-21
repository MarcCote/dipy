import numpy as np
import nibabel as nib
from nibabel import trackvis as tv
from dipy.segment.clustering import QuickBundles
from dipy.tracking.streamline import transform_streamlines, length
from dipy.viz import actor, window, widget
from dipy.viz import fvtk
from copy import copy, deepcopy
import os.path as path
from glob import glob
from dipy.io.trackvis import load_trk
from dipy.segment.bundles import qbx_with_merge
from ipdb import set_trace


def check_range(streamline, lt, gt):
    length_s = length(streamline)
    if (length_s < gt) & (length_s > lt):
        return True
    else:
        return False


def horizon(tractograms, data, affine, cluster=False, cluster_thr=15.,
            random_colors=False,
            length_lt=0, length_gt=np.inf, clusters_lt=0, clusters_gt=np.inf):

    slicer_opacity = .8

    ren = window.Renderer()
    global centroid_actors
    centroid_actors = []
    for streamlines in tractograms:

        print('Number of streamlines loaded {}'.format(len(streamlines)))

        if cluster:
            clusters = qbx_with_merge(streamlines,
                                      [60, 40, 30, 20, cluster_thr])
            centroids = clusters.centroids
            print('Number of centroids loaded {}'.format(len(centroids)))
            sizes = np.array([len(c) for c in clusters])
            linewidths = np.interp(sizes,
                                   [sizes.min(), sizes.max()], [0.1, 2.])
            visible_cluster_id = []

            for (i, c) in enumerate(centroids):
                # set_trace()
                if check_range(c, length_lt, length_gt):
                    if sizes[i] > clusters_lt and sizes[i] < clusters_gt:
                        act = actor.streamtube([c], linewidth=linewidths[i],
                                               lod=False)
                        centroid_actors.append(act)
                        ren.add(act)
                        visible_cluster_id.append(i)
        else:
            if not random_colors:
                ren.add(actor.line(streamlines,
                                   opacity=1., lod_points=10 ** 5))
            else:
                colors = np.random.rand(3)
                ren.add(actor.line(streamlines, colors,
                                   opacity=1., lod_points=10 ** 5))

    class SimpleTrackBallNoBB(window.vtk.vtkInteractorStyleTrackballCamera):
        def HighlightProp(self, p):
            pass

    style = SimpleTrackBallNoBB()
    # very hackish way
    style.SetPickColor(0, 0, 0)
    # style.HighlightProp(None)
    show_m = window.ShowManager(ren, size=(1200, 900), interactor_style=style)
    show_m.initialize()

    if data is not None:
        image_actor = actor.slicer(data, affine)
        image_actor.opacity(slicer_opacity)
        ren.add(image_actor)

        ren.add(fvtk.axes((10, 10, 10)))

        def change_slice(obj, event):
            z = int(np.round(obj.get_value()))
            image_actor.display(None, None, z)

        slider = widget.slider(show_m.iren, show_m.ren,
                               callback=change_slice,
                               min_value=0,
                               max_value=image_actor.shape[1] - 1,
                               value=image_actor.shape[1] / 2,
                               label="Move slice",
                               right_normalized_pos=(.98, 0.6),
                               size=(120, 0), label_format="%0.lf",
                               color=(1., 1., 1.),
                               selected_color=(0.86, 0.33, 1.))

    global size
    size = ren.GetSize()
    global picked_actors
    picked_actors = {}

    def pick_callback(obj, event):
        global centroid_actors
        global picked_actors

        prop = obj.GetProp3D()

        ac = np.array(centroid_actors)
        index = np.where(ac == prop)[0]

        if len(index) > 0:
            try:
                bundle = picked_actors[prop]
                ren.rm(bundle)
                del picked_actors[prop]
            except:
                bundle = actor.line(clusters[visible_cluster_id[index]],
                                    lod=False)
                picked_actors[prop] = bundle
                ren.add(bundle)

        if prop in picked_actors.values():
            ren.rm(prop)

    def win_callback(obj, event):
        global size
        if size != obj.GetSize():

            if data is not None:
                slider.place(ren)
            size = obj.GetSize()

    global centroid_visibility
    centroid_visibility = True

    def key_press(obj, event):
        global centroid_visibility
        key = obj.GetKeySym()
        if key == 'h' or key == 'H':
            if cluster:
                if centroid_visibility is True:
                    for ca in centroid_actors:
                        ca.VisibilityOff()
                    centroid_visibility = False
                else:
                    for ca in centroid_actors:
                        ca.VisibilityOn()
                    centroid_visibility = True
                show_m.render()

    show_m.initialize()
    show_m.iren.AddObserver('KeyPressEvent', key_press)
    show_m.add_window_callback(win_callback)
    show_m.add_picker_callback(pick_callback)
    show_m.render()
    show_m.start()


def horizon_flow(input_files, cluster=False, cluster_thr=15.,
                 random_colors=False, verbose=True,
                 length_lt=0, length_gt=1000,
                 clusters_lt=0, clusters_gt=10**7):
    """ Horizon

    Parameters
    ----------
    input_files : variable string
    cluster : bool, optional
    cluster_thr : float, optional
    random_colors : bool, optional
    verbose : bool, optional
    length_lt : float, optional
    length_gt : float, optional
    clusters_lt : int, optional
    clusters_gt : int, optional
    """

    filenames = input_files
    # glob(input_files)
    tractograms = []

    data = None
    affine = None
    for f in filenames:
        if verbose:
            print(f)
        sp = path.splitext(f)[1]

        if sp == '.trk':

            streamlines, hdr = load_trk(f)
            tractograms.append(streamlines)

        if sp == '.nii.gz' or sp == '.nii':

            img = nib.load(f)
            data = img.get_data()
            affine = img.get_affine()
            if verbose:
                print(affine)

    horizon(tractograms, data, affine, cluster, cluster_thr, random_colors,
            length_lt, length_gt, clusters_lt, clusters_gt)
