import numpy as np
import numpy.testing as npt
from dipy.segment.clustering import QuickBundles
from dipy.segment.clusteringspeed import evaluate_aabbb_checks
from dipy.data import get_data
import nibabel as nib
from dipy.tracking.streamline import set_number_of_points


def test_aabb_checks():
    A, B, res = evaluate_aabbb_checks()
    npt.assert_equal(res, 1)

def show_streamlines(streamlines, centroids):

    from dipy.viz import actor, window

    ren = window.Renderer()

    stream_actor = actor.line(streamlines)

    ren.add(stream_actor)

    window.show(ren)

    ren.clear()

    stream_actor2 = actor.line(centroids)

    ren.add(stream_actor2)
    window.show(ren)


def test_qbundles_aabb():
    streams, hdr = nib.trackvis.read(get_data('fornix'))
    streamlines = [s[0] for s in streams]

    for i in range(100):

        streamlines += [s[0] + np.array([i * 70, 0, 0]) for s in streams]


    from dipy.tracking.streamline import select_random_set_of_streamlines
    streamlines = select_random_set_of_streamlines(streamlines,
                                                   len(streamlines))

    print(len(streamlines))

    rstreamlines = set_number_of_points(streamlines, 20)

    from time import time

    qb = QuickBundles(5, bvh=False)
    t = time()
    clusters = qb.cluster(rstreamlines)
    print('Without BVH {}'.format(time() - t))
    print(len(clusters))

    show_streamlines(rstreamlines, clusters.centroids)

    qb = QuickBundles(5, bvh=True)
    t = time()
    clusters = qb.cluster(rstreamlines)
    print('With BVH {}'.format(time() - t))
    print(len(clusters))

    show_streamlines(rstreamlines, clusters.centroids)

    #from ipdb import set_trace
    #set_trace()


test_qbundles_aabb()