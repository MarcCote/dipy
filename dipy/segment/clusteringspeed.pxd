from cythonutils cimport Data2D, Shape, shape2tuple, tuple2shape
from metricspeed cimport Metric


cdef struct Streamline:
    Data2D features
    Data2D features_flip
    float[6] aabb
    int idx


cdef struct Centroid:
    Data2D features
    int size
    float[6] aabb

cdef struct NearestCluster:
    int id
    double dist
    int flip

cdef struct Test:
    Data2D centroid

cdef struct CentroidNode:
    CentroidNode* father
    CentroidNode** children
    int nb_children
    Data2D centroid
    float[6] aabb
    float threshold
    int* indices
    int size
    Shape centroid_shape
    int level



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


cdef class QuickBundlesX(object):
    cdef CentroidNode* root
    cdef Metric metric
    cdef Shape features_shape
    cdef Data2D features
    cdef Data2D features_flip
    cdef double* thresholds
    cdef int nb_levels
    cdef object level
    cdef object clusters

    cdef int _add_child_to(self, CentroidNode* node) nogil
    cdef void _update(self, CentroidNode* node) nogil
    cdef void _add_streamline_to(self, CentroidNode* node, Streamline* streamline, int flip) nogil
    cdef void _insert_in(self, CentroidNode* node, Streamline* streamline, int flip) nogil
    cdef void _insert(self, Streamline* streamline) nogil
    cpdef void insert(self, Data2D datum, int datum_idx)
    cdef void traverse_postorder(self, CentroidNode* node, void (*visit)(QuickBundlesX, CentroidNode*))
    cdef void _dealloc_node(self, CentroidNode* node)
    cdef void _fetch_level(self, CentroidNode* node)
