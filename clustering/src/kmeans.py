import os
from sklearn.cluster import KMeans
from sklearn import metrics
from sklearn.decomposition import PCA
import numpy as np
import matplotlib.pyplot as plt
import progressbar as pb
from progressbar import ProgressBar, ETA, Bar, Timer
# from collections import defaultdict
import argparse
import multiprocessing as mp
import yaml
import json
from collections import defaultdict
from cluster_visualizer import load_img

# CONSTANTS
K_START = 2
K_END = 10
TRIAL_NUM = 9
FIGURE_PATH = '../figures'
LABEL_PATH = '../labels'

def find_best_k(images, features_list_np, color_k='', prefix, show_plot=False):
    k_list = np.linspace(K_START, K_END, num=TRIAL_NUM, dtype=np.int32)

    silhouette_scores = []

    print('{} cores found.'.format(mp.cpu_count()))

    trial = 1
    progress = ProgressBar(widgets=[pb.Percentage(), ' ',  Bar('='), ' ', Timer()]).start()
    for k in progress(k_list):
        print('Clustering for K = {}...'.format(k))
        trial += 1
        # print(features_list_np)
        result = KMeans(n_clusters=k, random_state=0, n_jobs=-1, verbose=0).fit(features_list_np)
        labels = list(map(int, result.labels_))
        image_label_pairs = list(zip(images, labels))

        if not os.path.exists(LABEL_PATH):
            os.mkdir(LABEL_PATH)
        
        raw_label_file = open(os.path.join(LABEL_PATH,'{}_labels_{}.yml'.format(prefix, k)), 'w')
        # np.savetxt(labelfile, image_label_pairs)
        yaml.dump(image_label_pairs, raw_label_file, default_flow_style=False)
        raw_label_file.close()
        
        # Generate dict: cluster_label -> [images]
        cluster_dict = defaultdict(list)
        for pair in image_label_pairs:
            image = pair[0]
            label = pair[1]
            cluster_dict[label].append(image)
        # cluster_dict['n_clusters'] = k
        cluster_dict_json = open(os.path.join(LABEL_PATH, '{}_cluster_to_images_{}.json'.format(prefix, k)), 'w')
        json.dump(cluster_dict, cluster_dict_json)
        #cluster_dict_file = open(os.path.join(LABEL_PATH, 'VGG19_cluster_{}.yml'.format(k)), 'w')
        #yaml.dump(cluster_dict, cluster_dict_file, default_flow_style=False)

        # Silhouette score = [-1, 1]; -1 = incorrect clustering, 1 = highly dense clustering (well-separated)
        # Near 0 scores indicate overlapping clusters
        silhouette_scores.append(metrics.silhouette_score(features_list_np, labels, metric='euclidean'))

    print('Generating Silhouette Score vs. K Plot')
    # Plot Silhouette Score vs. K
    figure_sil = plt.figure(2)
    ax_sil = figure_sil.add_subplot(1, 1, 1)
    ax_sil.set_xlabel('K')
    ax_sil.set_ylabel('Silhouette Score')
    ax_sil.set_title('Silhouette Score vs. K')
    ax_sil.scatter(k_list, silhouette_scores)

    if not os.path.exists(FIGURE_PATH):
        os.mkdir(FIGURE_PATH)

    # Save plot and Silhouette scores
    plt.savefig(os.path.join(FIGURE_PATH, '{}_silhouette.png'.format(prefix))
    outfile = open(os.path.join(FIGURE_PATH, '{}_silhouette.txt'.format(prefix), 'w+')
    results = list(zip(k_list, silhouette_scores))
    #yaml.dump(results, outfile, default_flow_style=True)
    np.savetxt(outfile, results)
    outfile.close()

    if show_plot:
        plt.show()

    best_k = None
    best_score = float('-inf')
    for result in results:
        if best_score < result[1]:
            best_score = result[1]
            best_k = result[0]

    return best_k

def load_feature(filepath):
    return np.load(filepath)

# Dimensions = (4916, 11, 11, 512)
# Dominant color dimensions = (1000, 5, 3)
def main(**kwargs):
    imagepath = kwargs['image_path']
    filepath = kwargs['features_file']
    prefix  kwargs['prefix']
    pca_n = int(kwargs['pca'])
    #color_k = filepath.split('_')[-1][0]
    color_k = 'stats'
    images = os.listdir(imagepath)

    features_list = []
    if filepath: 
        features = load_feature(filepath)

        for i in range(features.shape[0]):
            features_list.append(features[i].flatten())
    else:
        features_list = load_img(imagepath)

    features_list_np = np.array(features_list)
    
    if pca_n > 0:
        pca = PCA(n_components=pca_n)
        features_list_np = pca.fit_transform(features_list_np)

        #Plotting the Cumulative Summation of the Explained Variance
        plt.figure(1)
        plt.plot(np.cumsum(pca.explained_variance_ratio_))
        plt.xlabel('Number of Components')
        plt.ylabel('Variance (%)') #for each component
        plt.title('Pulsar Dataset Explained Variance')
        plt.savefig(os.path.join(FIGURE_PATH, 'pca_exp_ratio.png'))
    
        print('PCA completed with %d components.' % (pca_n))

    print('Features loaded.')
    # print(features_list_np.shape)

    # print(color_k)

    best_k = find_best_k(images, features_list_np, color_k, prefix, kwargs['show_plot'])

    print('K_START: {}, K_END: {} -> Best K: {}'.format(K_START, K_END, best_k))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Takes in VGG-extracted features as input')
    parser.add_argument('image_path', help='Path to image data')
    parser.add_argument('features_file', nargs='?', help='File containing features', default=None)
    parser.add_argument('prefix', help='Prefix for figure and label naming', default='Prefix')
    parser.add_argument('--show_plot', help='Flag to enable showing plot', action='store_true', default=False)
    parser.add_argument('--pca', help='Flag for setting pca on or off', default=0)
    args = parser.parse_args()
    main(**vars(args))
