import os
import os.path
import logging
import logging.handlers

import xml.etree.ElementTree as ET

import math
import cv2 as cv

class TrainingDataGenerator():

    ''' Generates training images for the tree detection pipeline '''

    predefined_classes_file = "predefined_classes.txt"
    log_file_path = "training_data_generator.log"

    # defining image transformation parameters
    resized_width = 320
    resized_height = 240

    # defining sub block sizes (square)
    block_dim = 15
    min_block_covered_area = 0.5 * block_dim**2


    def __init__(self, scr_folder, target_folder):

        ''' 
        Inputs
        ------
        src_folder (str) : folder containing the labelled data files and the original images
        target_folder (str) : folder in which to create training images
        '''

        self.src_folder = scr_folder
        self.target_folder = target_folder

        # setting up logging
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        log_handler = logging.handlers.WatchedFileHandler(self.log_file_path)
        log_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(log_handler)

        # defining the predefined classes
        classes = []
        self.load_classes()


    def load_classes(self):

        ''' Loads classes from the predefined classes file'''

        try:
            with open(os.path.join(self.src_folder, self.predefined_classes_file)) as class_file_h:
                self.classes = class_file_h.readlines()
        except Exception as e:
            logging.error("TrainingDataGenerator failed to load the predefined classes  : {}".format(e))


    def generate_training_images(self):

        ''' Goes through all the annotation files and creates the proper training images in the target folder '''

        # going through the annotation data files in the scr folder
        for annotation_file in os.listdir(self.src_folder):
            if annotation_file.endswith(".xml"):

                try : 

                    # loading the current file xml
                    file_tree = ET.parse(os.path.join(self.src_folder, annotation_file)) 
                    file_root = file_tree.getroot()
        
                    # extracting dimension information
                    image_width = int(file_root.find('./size/width').text)
                    image_height = int(file_root.find('./size/height').text)
                    width_ratio = self.resized_width / image_width 
                    height_ratio = self.resized_height / image_height

                    # loading and resizing the referenced image
                    image_file_path = file_root.find('./path').text
                    image = cv.imread(image_file_path, cv.IMREAD_COLOR)
                    image = cv.resize(image, (self.resized_width, self.resized_height), 
                                         interpolation = cv.INTER_AREA)

                    # going through the labelled objects
                    for labeled_object in file_root.findall('./object'):

                        # extracting the label
                        object_label = labeled_object.find('./name').text

                        # extracting positional information
                        xmin = int(int(labeled_object.find('./bndbox/xmin').text) * width_ratio)
                        ymin = int(int(labeled_object.find('./bndbox/ymin').text) * height_ratio)
                        xmax = int(int(labeled_object.find('./bndbox/xmax').text) * width_ratio)
                        ymax = int(int(labeled_object.find('./bndbox/ymax').text) * height_ratio)

                        # calculating the possible horizontal indicies
                        min_row_pos = (ymin // self.block_dim) * self.block_dim
                        n_vertical_blocks = ((math.ceil(ymax / self.block_dim) * self.block_dim) - min_row_pos) // self.block_dim
                        min_col_pos = (xmin // self.block_dim) * self.block_dim
                        n_horizontal_blocks = ((math.ceil(xmax / self.block_dim) * self.block_dim) - min_col_pos) // self.block_dim

                        # going through the block touching the object
                        current_row = min_row_pos 
                        current_col = min_col_pos
                        for row_i  in range(n_vertical_blocks):
                            for col_i in range(n_horizontal_blocks):

                                # only processing blocks which contain enough "object matter"
                                 

                                # adding rectangle overlay on current block (testing)
                                start_point = (current_col, current_row)
                                end_point = (current_col + self.block_dim, current_row + self.block_dim)
                                image = cv.rectangle(image, start_point, end_point, (255, 0, 0), 2)                                

                                cv.imshow('image', image)  
                                cv.waitKey(0)

                                # moving to the next horizontal block
                                current_col += self.block_dim

                            # moving down a row of blocks
                            current_col = min_col_pos
                            current_row += self.block_dim

                        cv.destroyAllWindows()

                except Exception as e:
                    logging.error("TrainingDataGenerator failed while extracting data from label file : {0}, error : {1}\
                                  ".format(annotation_file, e))
                    raise