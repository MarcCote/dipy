import numpy as np

from dipy.segment.clusteringspeed import QuickBundlesX
from dipy.segment.metric import AveragePointwiseEuclideanMetric

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
