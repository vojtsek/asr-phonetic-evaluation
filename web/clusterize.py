#! /usr/bin/env python3
import sklearn.cluster
import numpy as np
import distance
from sklearn.feature_extraction.text import CountVectorizer

def get_for_cluster(cid, clustering, X):
    return X[clustering == cid]

X = []
with open('trns.out', 'r') as f:
    for line in f:
        X.append(line)
X = np.asarray(X)
lev_similarity = np.array([[distance.levenshtein(t1,t2) for t1 in X] for t2 in X])
n_cl=4

affprop = sklearn.cluster.AffinityPropagation(affinity="precomputed", damping=0.5)
affprop.fit(-1 * lev_similarity)
for cluster_id in np.unique(affprop.labels_):
    exemplar = X[affprop.cluster_centers_indices_[cluster_id]]
    cluster = np.unique(X[np.nonzero(affprop.labels_==cluster_id)])
    cluster_str = ", ".join(cluster)
    print(exemplar)
    for cl in cluster:
        print('\t' + cl)

spectral = sklearn.cluster.SpectralClustering(affinity="precomputed", n_clusters=n_cl)
spectral_clustering = spectral.fit_predict(lev_similarity)
for cl_id in range(n_cl):
    print(cl_id, get_for_cluster(cl_id, spectral_clustering, X))

vectorizer = CountVectorizer(min_df=1)
Xt = vectorizer.fit_transform(X)
kmeans = sklearn.cluster.KMeans(n_clusters=n_cl)
kmeans_clustering = kmeans.fit_predict(Xt)
for cl_id in range(n_cl):
    print(cl_id, get_for_cluster(cl_id, kmeans_clustering, X))
