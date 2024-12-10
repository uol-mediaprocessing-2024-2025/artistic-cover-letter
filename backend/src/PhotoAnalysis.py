import numpy as np
import os
from PIL import Image
import cv2
import matplotlib.pyplot as plt


from backend.src.testing import load_images_from_folder


def main():
    images = load_images_from_folder("C:/Users/Simon/Downloads/examplePhotos")

    image1 = cv2.imread("C:/Users/Simon/Downloads/examplePhotos/P1040723.jpg")
    image2 = cv2.imread("C:/Users/Simon/Downloads/examplePhotos/P1040731.jpg")
    image3 = cv2.imread("C:/Users/Simon/Downloads/examplePhotos/P1040740.jpg")
    image4 = cv2.imread("C:/Users/Simon/Downloads/examplePhotos/P1040798.jpg")

    print(" ------- comparing P1040723 and P1040731 ------- ")
    compare_histograms(image1, image2) # quite similar

    print(" ------- comparing P1040723 and P1040740 ------- ")
    compare_histograms(image1, image3) # much less similar

    print(" ------- comparing P1040723 with itself ------- ")
    compare_histograms(image1, image1)

    print(average_hue(Image.fromarray(image4)))
    draw_hue_histogram(image4)
    draw_hue_histogram_2(image4)


def compare_histograms(image1, image2):
    # AI generated histogram code to quickly test different methods


    # Calculate histogram for each color channel (B, G, R)
    hist1_b = cv2.calcHist([image1], [0], None, [256], [0, 256])
    hist1_g = cv2.calcHist([image1], [1], None, [256], [0, 256])
    hist1_r = cv2.calcHist([image1], [2], None, [256], [0, 256])

    hist2_b = cv2.calcHist([image2], [0], None, [256], [0, 256])
    hist2_g = cv2.calcHist([image2], [1], None, [256], [0, 256])
    hist2_r = cv2.calcHist([image2], [2], None, [256], [0, 256])

    # Normalize histograms
    hist1_b = cv2.normalize(hist1_b, hist1_b).flatten()
    hist1_g = cv2.normalize(hist1_g, hist1_g).flatten()
    hist1_r = cv2.normalize(hist1_r, hist1_r).flatten()

    hist2_b = cv2.normalize(hist2_b, hist2_b).flatten()
    hist2_g = cv2.normalize(hist2_g, hist2_g).flatten()
    hist2_r = cv2.normalize(hist2_r, hist2_r).flatten()

    # Method 1: Correlation
    correlation_b = cv2.compareHist(hist1_b, hist2_b, cv2.HISTCMP_CORREL)
    correlation_g = cv2.compareHist(hist1_g, hist2_g, cv2.HISTCMP_CORREL)
    correlation_r = cv2.compareHist(hist1_r, hist2_r, cv2.HISTCMP_CORREL)

    # Method 2: Chi-Square
    chi_square_b = cv2.compareHist(hist1_b, hist2_b, cv2.HISTCMP_CHISQR)
    chi_square_g = cv2.compareHist(hist1_g, hist2_g, cv2.HISTCMP_CHISQR)
    chi_square_r = cv2.compareHist(hist1_r, hist2_r, cv2.HISTCMP_CHISQR)

    # Method 3: Intersection
    intersection_b = cv2.compareHist(hist1_b, hist2_b, cv2.HISTCMP_INTERSECT)
    intersection_g = cv2.compareHist(hist1_g, hist2_g, cv2.HISTCMP_INTERSECT)
    intersection_r = cv2.compareHist(hist1_r, hist2_r, cv2.HISTCMP_INTERSECT)

    # Method 4: Bhattacharyya Distance
    bhattacharyya_b = cv2.compareHist(hist1_b, hist2_b, cv2.HISTCMP_BHATTACHARYYA)
    bhattacharyya_g = cv2.compareHist(hist1_g, hist2_g, cv2.HISTCMP_BHATTACHARYYA)
    bhattacharyya_r = cv2.compareHist(hist1_r, hist2_r, cv2.HISTCMP_BHATTACHARYYA)

    correlation_average = (abs(correlation_b) + abs(correlation_g) + abs(correlation_r))/3
    chi_square_average = (abs(chi_square_b) + abs(chi_square_g) + abs(chi_square_r))/3
    intersection_average = (abs(intersection_b) + abs(intersection_g) + abs(intersection_r))/3
    bhattacharyya_average =  (abs(bhattacharyya_b) + abs(bhattacharyya_g) + abs(bhattacharyya_r))/3

    print(f'Correlation avg: {correlation_average}')
    print(f'Chi-Square avg: {chi_square_average}')
    print(f'Intersection avg: {intersection_average}')
    print(f'Bhattacharyya avg: {bhattacharyya_average}')

def average_hue(image):

    # Convert the image to HSV
    hsv_image = image.convert('HSV')

    # Extract the H channel (Hue)
    hue_data = np.array(hsv_image)[:, 0, 0]  # H channel is the first channel in HSV

    # Calculate the average hue
    average_hue = np.mean(hue_data)

    return average_hue


def draw_hue_histogram(image):

    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Extract the hue channel
    hue_channel = hsv_image[:, :, 0]

    plt.imshow(hue_channel)

    # Calculate the histogram for the hue channel
    hist = cv2.calcHist([hue_channel], [0], None, [180], [0, 180])

    # Plot the histogram using matplotlib
    plt.figure(figsize=(10, 6))
    plt.title('Hue Histogram')
    plt.xlabel('Hue Value')
    plt.ylabel('Frequency')
    plt.plot(hist, color='orange')
    plt.xlim([0, 180])
    plt.show()

def draw_hue_histogram_2(image):
    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Extract the hue, saturation, and value channels
    hue_channel = hsv_image[:, :, 0]
    saturation_channel = hsv_image[:, :, 1]
    value_channel = hsv_image[:, :, 2]

    # Create a mask for pixels with brightness (value) greater than x
    brightness_mask = value_channel > 140

    # Apply the mask to the hue channel
    hue_channel_filtered = hue_channel[brightness_mask]

    # Calculate the histogram for the filtered hue channel
    hist = cv2.calcHist([hue_channel_filtered], [0], None, [180], [0, 180])

    # Plot the histogram using matplotlib
    plt.figure(figsize=(10, 6))
    plt.title('Hue Histogram (Brightness > x')
    plt.xlabel('Hue Value')
    plt.ylabel('Frequency')
    plt.plot(hist, color='orange')
    plt.xlim([0, 180])
    plt.show()

if __name__ == '__main__':
    main()