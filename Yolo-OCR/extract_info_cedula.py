# Extraer bounding boxes
from pytesseract import Output
import pytesseract
# import imutils
# import argparse
import os
import glob
import random
import darknet
# import time
import cv2
import numpy as np
import darknet
# import matplotlib.pyplot as plt

# def parser():
#     parser = argparse.ArgumentParser(description="YOLO Object Detection")
#     parser.add_argument("--input_file", type=str, default="",
#                         help="image source. It can be a single image, a"
#                         "txt with paths to them, or a folder. Image valid"
#                         " formats are jpg, jpeg or png."
#                         "If no input is given, ")
#     parser.add_argument("--batch_size", default=1, type=int,
#                         help="number of images to be processed at the same time")
#     parser.add_argument("--weights", default="yolov4.weights",
#                         help="yolo weights path")
#     parser.add_argument("--config_file", default="./cfg/yolov4.cfg",
#                         help="path to config file")
#     parser.add_argument("--data_file", default="./cfg/coco.data",
#                         help="path to data file")
#     parser.add_argument("--thresh", type=float, default=.25,
#                         help="remove detections with lower confidence")
#     return parser.parse_args()

def check_batch_shape(images, batch_size):
    """
        Image sizes should be the same width and height
    """
    shapes = [image.shape for image in images]
    if len(set(shapes)) > 1:
        raise ValueError("Images don't have same shape")
    if len(shapes) > batch_size:
        raise ValueError("Batch size higher than number of images")
    return shapes[0]


def load_images(images_path):
    """
    If image path is given, return it directly
    For txt file, read it and return each line as image path
    In other case, it's a folder, return a list with names of each
    jpg, jpeg and png file
    """
    input_path_extension = images_path.split('.')[-1]
    if input_path_extension in ['jpg', 'jpeg', 'png']:
        return [images_path]
    elif input_path_extension == "txt":
        with open(images_path, "r") as f:
            return f.read().splitlines()
    else:
        return glob.glob(
            os.path.join(images_path, "*.jpg")) + \
            glob.glob(os.path.join(images_path, "*.png")) + \
            glob.glob(os.path.join(images_path, "*.jpeg"))


def prepare_batch(images, network, channels=3):
    width = darknet.network_width(network)
    height = darknet.network_height(network)

    darknet_images = []
    for image in images:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_resized = cv2.resize(image_rgb, (width, height),
                                   interpolation=cv2.INTER_LINEAR)
        custom_image = image_resized.transpose(2, 0, 1)
        darknet_images.append(custom_image)

    batch_array = np.concatenate(darknet_images, axis=0)
    batch_array = np.ascontiguousarray(batch_array.flat, dtype=np.float32)/255.0
    darknet_images = batch_array.ctypes.data_as(darknet.POINTER(darknet.c_float))
    return darknet.IMAGE(width, height, channels, darknet_images)


def image_detection(image, network, class_names, class_colors, thresh):
    # Darknet doesn't accept numpy images.
    # Create one with image we reuse for each detect
    width = darknet.network_width(network)
    height = darknet.network_height(network)
    darknet_image = darknet.make_image(width, height, 3)

    # image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_resized = cv2.resize(image_rgb, (width, height),
                               interpolation=cv2.INTER_LINEAR)

    darknet.copy_image_from_bytes(darknet_image, image_resized.tobytes())
    detections = darknet.detect_image(network, class_names, darknet_image, thresh=thresh)
    darknet.free_image(darknet_image)
    image = darknet.draw_boxes(detections, image_resized, class_colors)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB), detections


def batch_detection(network, images, class_names, class_colors,
                    thresh=0.25, hier_thresh=.5, nms=.45, batch_size=4):
    image_height, image_width, _ = check_batch_shape(images, batch_size)
    darknet_images = prepare_batch(images, network)
    batch_detections = darknet.network_predict_batch(network, darknet_images, batch_size, image_width,
                                                     image_height, thresh, hier_thresh, None, 0, 0)
    batch_predictions = []
    for idx in range(batch_size):
        num = batch_detections[idx].num
        detections = batch_detections[idx].dets
        if nms:
            darknet.do_nms_obj(detections, num, len(class_names), nms)
        predictions = darknet.remove_negatives(detections, class_names, num)
        images[idx] = darknet.draw_boxes(predictions, images[idx], class_colors)
        batch_predictions.append(predictions)
    darknet.free_batch_detections(batch_detections, batch_size)
    return images, batch_predictions


def image_classification(image, network, class_names):
    width = darknet.network_width(network)
    height = darknet.network_height(network)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_resized = cv2.resize(image_rgb, (width, height),
                                interpolation=cv2.INTER_LINEAR)
    darknet_image = darknet.make_image(width, height, 3)
    darknet.copy_image_from_bytes(darknet_image, image_resized.tobytes())
    detections = darknet.predict_image(network, darknet_image)
    predictions = [(name, detections[idx]) for idx, name in enumerate(class_names)]
    darknet.free_image(darknet_image)
    return sorted(predictions, key=lambda x: -x[1])


def convert2relative(image, bbox):
    """
    YOLO format use relative coordinates for annotation
    """
    x, y, w, h = bbox
    height, width, _ = image.shape
    return x/width, y/height, w/width, h/height

def save_annotations(name, image, detections, class_names):
    """
    Files saved with image_name.txt and relative coordinates
    """
    file_name = os.path.splitext(name)[0] + ".txt"
    with open(file_name, "w") as f:
        for label, confidence, bbox in detections:
            x, y, w, h = convert2relative(image, bbox)
            label = class_names.index(label)
            f.write("{} {:.4f} {:.4f} {:.4f} {:.4f} {:.4f}\n".format(label, x, y, w, h, float(confidence)))


def batch_detection_example():
    args = parser()
    check_arguments_errors(args)
    batch_size = 3
    random.seed(3)  # deterministic bbox colors
    network, class_names, class_colors = darknet.load_network(
        args.config_file,
        args.data_file,
        args.weights,
        batch_size=batch_size
    )
    image_names = ['data/horses.jpg', 'data/horses.jpg', 'data/eagle.jpg']
    images = [cv2.imread(image) for image in image_names]
    images, detections,  = batch_detection(network, images, class_names,
                                           class_colors, batch_size=batch_size)
    for name, image in zip(image_names, images):
        cv2.imwrite(name.replace("data/", ""), image)
    print(detections)

def extract_info_cedula(image, detections, img_cedula_raw):
#   img_cedula_raw = cv2.imread(image_name)
  img_cedula_raw = cv2.cvtColor(img_cedula_raw, cv2.COLOR_BGR2RGB)
  hmax,wmax,_=img_cedula_raw.shape
  requeriments=['nombres', 'numero', 'apellidos', 'cedula']
  names = [detection[0] for detection in detections]
  names = np.unique(names)
  if set(requeriments)-set(names) != set():
    log = 'Extracted box {}'.format(names)
  else:
    names_to_extract_info=['nombres', 'numero', 'apellidos']
    log = 'Extracted box {}'.format(names)
  results_dict={}
  for j in range(len(detections)):
    x, y, w, h = convert2relative(image, detections[j][-1])
    if not detections[j][0] in names_to_extract_info:
      continue
    xmin=int((x-(w/2))*wmax)-int((0.05*(x-(w/2))*wmax))
    ymin=int((y-(h/2))*hmax)
    xmax=int((x+(w/2))*wmax)+int((0.05*(x+(w/2))*wmax))
    ymax=int((y+(h/2))*hmax)
    roi=img_cedula_raw[ymin:ymax,xmin:xmax,:]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    custom_config = r'--psm 6 --l spa'
    #text = pytesseract.image_to_string(gray,config=custom_config)
    d = pytesseract.image_to_data(gray,config=custom_config,output_type=Output.DICT)
    #binary2=gray
    n_boxes = len(d['text'])
    extracted_text=[]
    ylist=[]
    hlist=[]
    #plt.imshow(gray,'gray')
    #plt.show()
    for i in range(n_boxes):
        if int(d['conf'][i]) >= 0:
            (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
            extracted_text.append(d['text'][i])
            ylist.append(y)
            hlist.append(h)
            #binary2 = cv2.rectangle(binary2, (x, y), (x + w, y + h), (0, 255, 0), 2)
    idx=[]
    for yy in ylist:
      if abs(np.min(ylist)-yy)< np.max(hlist)/2:
        idx.append(True)
      else:
        idx.append(False)
    if detections[j][0]=='numero':
      real_info = [''.join(e for e in text if e.isnumeric()) for text,idx in zip(extracted_text,idx) if idx]
      real_info = ''.join(real_info)
    else:
      real_info = [''.join(e for e in text if e.isalpha()) for text,idx in zip(extracted_text,idx) if idx]
      real_info = ' '.join(real_info)
      real_info = [info for info in real_info.split(' ') if len(info)>2]
      real_info = ' '.join(real_info)
    results_dict[detections[j][0]]=real_info.upper()
  return results_dict, log

class main_cedula():
    def __init__(self,config_file,data_file,weights,
                thresh):
        self.config_file=config_file
        self.data_file=data_file
        self.weights=weights
        self.thresh=thresh

    def load_darknet(self,):
        random.seed(0)  # deterministic bbox colors
        self.network, self.class_names, self.class_colors = darknet.load_network(
            self.config_file,
            self.data_file,
            self.weights,
            batch_size=1
        )

    def main_cedula_run(self,image_raw):
        image, detections = image_detection(
            image_raw, self.network, self.class_names, self.class_colors, self.thresh
            )
        results_dict, log = extract_info_cedula(image, detections, image_raw)
        #print(results_dict)
        return results_dict, log  

# if __name__ == "__main__":
#     # unconmment next line for an example of batch processing
#     # batch_detection_example()
#     main()