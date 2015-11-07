import numpy as np

from dipy.segment.clusteringspeed import QuickBundlesX
from dipy.segment.metric import AveragePointwiseEuclideanMetric
from dipy.tracking.streamline import set_number_of_points
from dipy.data import get_data
import nibabel.trackvis as tv


def test_basic_qbx():

    feature_shape = (10, 3)
    streamlines = [np.ones((10, 3), dtype="f4")]
    #test_hqb(streamlines, AveragePointwiseEuclideanMetric())

    feature_shape = (1, 3)
    points = np.array([[[1, 1, 0]],
                       [[3, 1, 0]],
                       [[2, 1, 0]],
                       [[5, 1, 0]],
                       [[5.5, 1, 0]]], dtype="f4")

    thresholds = [4, 2, 1]
    qbx = QuickBundlesX(feature_shape, thresholds, AveragePointwiseEuclideanMetric())
    print(qbx)

    for i, p in enumerate(points):
        print "\nInserting {}".format(p)
        qbx.insert(p, np.int32(i))
        print(qbx)


def simulated_bundle(no_streamlines=10, waves=False, no_pts=12):
    t = np.linspace(-10, 10, 200)
    # parallel waves or parallel lines
    bundle = []
    for i in np.linspace(-5, 5, no_streamlines):
        if waves:
            pts = np.vstack((np.cos(t), t, i * np.ones(t.shape))).T
        else:
            pts = np.vstack((np.zeros(t.shape), t, i * np.ones(t.shape))).T
        pts = set_number_of_points(pts, no_pts)
        bundle.append(pts)

    return bundle


def fornix_streamlines(no_pts=12):
    fname = get_data('fornix')
    streams, hdr = tv.read(fname)
    streamlines = [set_number_of_points(i[0], no_pts) for i in streams]
    return streamlines


def test_with_simulated_bundles():

    streamlines = simulated_bundle(100, False, 20)

    from dipy.viz import actor, window

    renderer = window.Renderer()
    bundle_actor = actor.line(streamlines)
    renderer.add(bundle_actor)

    window.show(renderer)


if __name__ == '__main__':

    test_with_simulated_bundles()

