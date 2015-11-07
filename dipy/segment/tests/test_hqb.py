import numpy as np

from dipy.segment.clusteringspeed import HierarchicalQuickBundles
from dipy.segment.metric import AveragePointwiseEuclideanMetric

feature_shape = (10, 3)
streamlines = [np.ones((10, 3), dtype="f4")]
#test_hqb(streamlines, AveragePointwiseEuclideanMetric())

feature_shape = (1, 3)
points = np.array([[[1, 0, 0]],
                   [[3, 0, 0]],
                   [[2, 0, 0]],
                   [[5, 0, 0]],
                   [[5.5, 0, 0]]], dtype="f4")

hqb = HierarchicalQuickBundles(feature_shape, AveragePointwiseEuclideanMetric(), 1)
print(hqb)

for i, p in enumerate(points):
    print "\nInserting {}".format(p)
    hqb.insert(p, np.int32(i))
    print(hqb)
