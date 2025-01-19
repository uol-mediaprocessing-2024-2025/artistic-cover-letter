from time import sleep

import colorspacious as cs
import matplotlib.colors as matcolors
import numpy as np
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans

def cluster_photos(photo_colors):
    distance_matrix = np.zeros((len(photo_colors), len(photo_colors)))
    print("Calculating distance matrix... ")
    for i in range(len(photo_colors)):
        for j in range(i, len(photo_colors)):
            if i == j:
                distance_matrix[i, j] = 0
            else:
                distance = rate_photo_pairing(photo_colors[i], photo_colors[j])
                distance_matrix[i, j] = distance
                distance_matrix[j, i] = distance  # Matrix symmetry

    print("Performing clustering... ")
    cluster_count = int(len(photo_colors)/10)

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
        scores.append(rate_photo_pairing(color_scheme, photo_scheme))
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
def rate_photo_pairing(color_scheme, photo_scheme):
    total_score = 0
    for color in color_scheme:
        best = 30000
        for photo_color in photo_scheme:
            score = rate_color_pairing(color, photo_color)
            if score < best:
                best = score
        total_score = total_score + best
    return total_score

# This method rates the distance between two colors based on Euclidean distance in CIELab.
def rate_color_pairing(color_scheme, photo_color):
    photo_color_lab = cs.cspace_convert(photo_color, "sRGB1", "CIELab")
    color_scheme_lab = cs.cspace_convert(color_scheme, "sRGB1", "CIELab")
    distance = np.linalg.norm(color_scheme_lab - photo_color_lab)
    return distance




# Takes in an RGB color and varies all HSV dimensions except the one that
# is given in constant_dimension
def generate_hsv_variations(color, constant_dimension):
    color = np.array(color)
    normalized = color/255.0
    hsv = matcolors.rgb_to_hsv(normalized)
    constant = hsv[constant_dimension]
    hsv = np.delete(hsv, constant_dimension)
    variable1 = hsv[0]
    variable2 = hsv[1]
    depth = 8
    colors = []
    for variable1_offset in range(1,depth):
        variable1_offset = (variable1_offset / depth)/5
        # Ensure that variable 1 is within 0 and 1
        if ((variable1 + (-2) * variable1_offset) > 0) & (variable1 + 2 * variable1_offset < 1):
            for variable2_offset in range(1,depth):
                variable2_offset = (variable2_offset / depth)/5
                # Ensure that variable 2 is within 0 and 1
                if ((variable2 + (-2) * variable2_offset) > 0) & (variable2 + 2 * variable2_offset < 1):
                    color_scheme = []
                    for pallet_offset in range(5):
                        hsv_variable1 = variable1 + ((pallet_offset - 2) * variable1_offset)
                        hsv_variable2 = variable2 + ((pallet_offset - 2) * variable2_offset)
                        match constant_dimension:
                            case 0: hsv = np.array([constant, hsv_variable1, hsv_variable2])
                            case 1: hsv = np.array([hsv_variable1, constant, hsv_variable2])
                            case 2: hsv = np.array([hsv_variable1, hsv_variable2, constant])
                        rgb = matcolors.hsv_to_rgb(hsv)
                        rgb = (rgb*255).astype(np.uint8)
                        color_scheme.append(rgb)
                    colors.append(color_scheme)
    return colors


def generate_constant_value(value):
    colors = []
    for hue in range(0, 7):
        for saturation in range(0, 7):
            hue = hue*(365/8)
            rad = np.deg2rad(hue)
            a = 100 * np.cos(rad)
            b = 100 * np.sin(rad)
            value = 1
            a = 0
            b = 0
            cielab = np.array([value, a, b])
            rgb = cs.cspace_convert(cielab, "CIELab", "sRGB1")
            print(rgb)
            colors.append(rgb)
    return colors

# Plot the colors as bar chart for testing. Bing AI Method
def plot_colors(colors):
    fig, ax = plt.subplots(1, 1, figsize=(8, 2), subplot_kw=dict(xticks=[], yticks=[], frame_on=False))
    ax.imshow([colors], aspect='auto')
    plt.show()