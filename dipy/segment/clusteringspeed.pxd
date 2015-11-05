from cythonutils cimport Data2D, Shape, shape2tuple, tuple2shape
from metricspeed cimport Metric


cdef struct Centroid:
    Data2D features
    int size
    float[6] aabb

cdef struct NearestCluster:
    int id
    double dist


cdef class Clusters:
    cdef int _nb_clusters
    cdef int** clusters_indices
    cdef int* clusters_size

    cdef void c_assign(Clusters self, int id_cluster, int id_element, Data2D element) nogil except *
    cdef int c_create_cluster(Clusters self) nogil except -1
    cdef int c_size(Clusters self) nogil


cdef class ClustersCentroid(Clusters):
    cdef Centroid* centroids
    cdef Centroid* _updated_centroids
    cdef Shape _centroid_shape
    cdef float eps
    cdef void c_assign(ClustersCentroid self, int id_cluster, int id_element, Data2D element) nogil except *
    cdef int c_create_cluster(ClustersCentroid self) nogil except -1
    cdef int c_update(ClustersCentroid self, int id_cluster) nogil except -1


cdef class QuickBundles(object):
    cdef Shape features_shape
    cdef Data2D features
    cdef Data2D features_flip
    cdef ClustersCentroid clusters
    cdef Metric metric
    cdef double threshold
    cdef double aabb_pad
    cdef int max_nb_clusters
    cdef int bvh

    cdef NearestCluster find_nearest_cluster(QuickBundles self, Data2D features) nogil except *
    cdef int assignment_step(QuickBundles self, Data2D datum, int datum_id) nogil except -1
    cdef void update_step(QuickBundles self, int cluster_id) nogil except *
