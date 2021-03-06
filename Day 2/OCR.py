import imutils
import numpy as np
import matplotlib.pyplot as plt
from skimage.filters import threshold_local
import cv2
import pytesseract
from pdf2image import convert_from_path


def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped


def Image_filter(img_address):
    image = cv2.imread(img_address)
    try:
        if image == None:
            image = plt.imread(img_address)
    except:
        pass
    image = cv2.copyMakeBorder(image.copy(), 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[1, 1, 1])
    ratio = image.shape[0] / 500.0
    orig = image.copy()
    image = imutils.resize(image, height=500)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 120, 200)
    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4:
            screenCnt = approx
            break

    cv2.drawContours(image, [screenCnt], -1, (0, 255, 0), 2)
    warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)
    warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    T = threshold_local(warped, 9, offset=7, method="gaussian")
    warped = (warped > T).astype("uint8") * 255
    img = warped.copy()
    kernel = np.ones((1, 1), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)
    img = cv2.erode(img, kernel, iterations=1)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    plt.imsave('sharp_img.png', img, cmap = 'gray')
    plt.imshow(img, cmap='gray')
    plt.show()


def pdf_ocr(path, langs):
    pages = convert_from_path(path, poppler_path='C:\\Users\\Shiv\\PycharmProjects\\Shiv\\Django_Prjct\\first_app\\poppler-0.68.0\\bin')
    image_counter = 1
    for page in pages:
        filename = "page" + str(image_counter) + ".jpg"
        page.save(filename, 'JPEG')
        image_counter = image_counter + 1

    cfg = '-l ' + langs    # -l tel+urd

    for i in range(1, image_counter):
        filename = "page" + str(i) + ".jpg"
        img = Image_filter(filename)
        text = str(pytesseract.image_to_string(img, config=cfg))
        text = text.replace('-\n', '')
    return text


def img_ocr(file, langs):
    img = Image_filter(file)
    cfg = '-l ' + langs
    out = pytesseract.image_to_string(img, config=cfg)
    return out

