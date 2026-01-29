import colorspacious as cs
import joblib
import matplotlib.colors as matcolors
import numpy as np
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans
import os
# Fixes a really bad deadlock when running sklearn in parallel
os.environ["LOKY_MAX_CPU_COUNT"] = "4"
os.environ["OMP_NUM_THREADS"] = "4"
os.environ["OPENBLAS_NUM_THREADS"] = "4"

# Uses an Algorithm by Kamal Joshi to find prominent colors.
# https://hackernoon.com/extract-prominent-colors-from-an-image-using-machine-learning-vy2w33rx
def get_image_colors(image):
    image = np.array(image)

    # Reshape image to a 2D array of pixels
    srgb_pixels = image.reshape(-1, 3)
    lab_pixels = cs.cspace_convert(srgb_pixels, "sRGB1", "CIELab")

    # Run k-means clustering
    kmeans = KMeans(n_clusters=24, init='k-means++', n_init=14, max_iter=450, random_state=42)
    kmeans.fit(lab_pixels)

    # Get the cluster centers (dominant colors)
    colors = kmeans.cluster_centers_
    colors = cs.cspace_convert(colors, "CIELab", "sRGB1")

    # Convert color to integer values
    colors_rgb = [list(map(int, color)) for color in colors]

    # Sort by hue
    hue_sorted = sort_colors_by_hsv_component(colors_rgb, 0)

    # Split into six groups
    group1 = hue_sorted[0:4]
    group2 = hue_sorted[4:8]
    group3 = hue_sorted[8:12]
    group4 = hue_sorted[12:16]
    group5 = hue_sorted[16:20]
    group6 = hue_sorted[20:24]

    groups = [group1, group2, group3, group4, group5, group6]
    groupresults = []

    # Perform other group operations
    for group in groups:
        group = sort_colors_by_hsv_component(group, 1)
        group = group[2:4]
        group = sort_colors_by_hsv_component(group, 2)
        groupresults.append(group[1])
    return groupresults

# Sorts an array of colors by one of the three HSV components specified by the dimension parameter
def sort_colors_by_hsv_component(rgb_colors, dimension):
    # normalize rgb and convert to hsv
    normalized = np.array(rgb_colors) / 255.0
    hsv_colors = [matcolors.rgb_to_hsv(color) for color in normalized]

    # Sort the colors by the hue component (first value in HSB)
    sorted_indices = np.argsort([color[dimension] for color in hsv_colors])

    # Return the colors sorted by hue
    return [rgb_colors[i] for i in sorted_indices]

# Clusters photos to generate groups of photos with a color scheme each
def cluster_photos(photo_colors):
    n = len(photo_colors)
    distance_matrix = np.zeros((n, n))
    print("Calculating distance matrix... ")
    for i in range(n):
        for j in range(i, n):
            if i != j:
                distance = rate_scheme_pairing(photo_colors[i], photo_colors[j])
                distance_matrix[i, j] = distance
                distance_matrix[j, i] = distance  # Matrix symmetry
    print("Performing clustering... ")
    cluster_count = int(len(photo_colors)/10)
    if cluster_count < 1: cluster_count = 1

    kmeans = KMeans(n_clusters=cluster_count, init='k-means++', n_init=128, max_iter=256)
    cluster_assignments = kmeans.fit_predict(distance_matrix)
    cluster_centers = kmeans.cluster_centers_
    closest_points = find_closest_points(cluster_centers, distance_matrix)

    groups = []
    for integer in range(0, cluster_count):
        cluster_group = []
        for index in range(0, len(cluster_assignments)):
            if cluster_assignments[index] == integer:
                cluster_group.append(index)
        groups.append(cluster_group)

    schemes = []
    for index in closest_points:
        colors = photo_colors[index]
        hex_colors = []
        for color in colors:
            hex_colors.append('#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2]))
        schemes.append(hex_colors)
    print("Done!")
    return schemes, groups

    # Takes cluster centers and uses the distance matrix to find the center cluster element.
    # Written by Bing AI

def find_closest_points(cluster_centers, distance_matrix):
    closest_points = []
    for center in cluster_centers:
        distances = np.linalg.norm(distance_matrix - center, axis=1)
        closest_point = np.argmin(distances)
        closest_points.append(closest_point)
    return closest_points

# takes the input of all prominent colors in all images and uses k-means clustering
# to find n number of colors where n is equal to the number of images.
# This is used to later find color schemes with those colors.
def get_frequent_colors(colors):
    count = min(len(colors), 270)
    colors = colors.reshape(-1, 3)
    lab_pixels = cs.cspace_convert(colors, "sRGB1", "CIELab")
    kmeans = KMeans(n_clusters=count)
    kmeans.fit(lab_pixels)
    colors = kmeans.cluster_centers_
    colors = cs.cspace_convert(colors, "CIELab", "sRGB1")
    colors_rgb = [list(map(int, color)) for color in colors]
    return colors_rgb

# Takes a color as a starting value and will generate various color schemes with
# a score to rate how well it fits the actual photos.
def generate_color_schemes(frequent_color, photo_colors, photo_count):
    schemes = []
    # Generate color schemes
    for scheme in generate_hsv_variations(frequent_color, 0):
        schemes.append(scheme)
    for scheme in generate_hsv_variations(frequent_color, 1):
        schemes.append(scheme)
    for scheme in generate_hsv_variations(frequent_color, 2):
        schemes.append(scheme)

    all_scores = []
    best_schemes = []
    best_schemes_pallet = []
    for i, color_scheme in enumerate(schemes):
        score_final, indices = rate_color_scheme(color_scheme, photo_colors, photo_count)
        all_scores.append(score_final)
        best_schemes.append(indices)
        best_schemes_pallet.append(color_scheme)
    combined_sorted = sorted(zip(all_scores, best_schemes, best_schemes_pallet), reverse=True)
    all_scores_sorted, best_schemes_sorted, best_schemes_pallet_sorted = map(list, zip(*combined_sorted))
    return best_schemes_sorted, best_schemes_pallet_sorted, all_scores_sorted

# This method rates a color scheme based on colors from a number of photos.
# color_scheme: a generated scheme of 5 colors
# photo_colors: an array of photo colors
def rate_color_scheme(color_scheme, photo_colors, photo_count):
    scores = []
    indices = []
    for index, photo_scheme in enumerate(photo_colors):
        scores.append(rate_scheme_pairing(color_scheme, photo_scheme))
        indices.append(index)
    combined_sorted = sorted(zip(scores, indices), reverse=True)
    scores_sorted, indices_sorted = map(list, zip(*combined_sorted))
    score_final = 0
    indices_final = []
    for index in range(0, photo_count):
        score_final = score_final + scores_sorted[index]
        indices_final.append(indices_sorted[index])
    return score_final, indices_final

# This method rates the pairing between two color schemes using the rate_color_pairing
# method to assess each color pairing.
def rate_scheme_pairing(scheme_1, scheme_2):
    total_score = 0
    for color_1 in scheme_1:
        best = 30000
        for color_2 in scheme_2:
            score = rate_color_pairing(color_1, color_2)
            if score < best:
                best = score
        total_score = total_score + best
    return total_score

# This method rates the distance between two colors based on Euclidean distance in CIELab.
def rate_color_pairing(color_1, color_2):
    photo_color_lab = cs.cspace_convert(color_2, "sRGB1", "CIELab")
    color_scheme_lab = cs.cspace_convert(color_1, "sRGB1", "CIELab")
    distance = np.linalg.norm(color_scheme_lab - photo_color_lab)
    return distance

# Plot the colors as bar chart for testing. Bing AI Method
def plot_colors(colors):
    fig, ax = plt.subplots(1, 1, figsize=(8, 2), subplot_kw=dict(xticks=[], yticks=[], frame_on=False))
    ax.imshow([colors], aspect='auto')
    plt.show()