import os
import logging
from typing import List, Set, Dict
import pandas as pd
from ultralytics import YOLO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# The nano model was selected for efficient local processing
model = YOLO('yolov8n.pt')


def classify_image(detected_objects: Set[str]) -> str:
    """
    Classify an image into a category based on detected objects.

    Categories:
    - 'promotional': Both person and product detected
    - 'product_display': Product detected, no person
    - 'lifestyle': Person detected, no product
    - 'other': Neither person nor product detected

    Args:
        detected_objects (Set[str]): Set of object labels detected in the image.

    Returns:
        str: Image category.
    """
    products = {'bottle', 'cup', 'wine glass', 'vase'}
    has_person = 'person' in detected_objects
    has_product = any(obj in products for obj in detected_objects)

    if has_person and has_product:
        return 'promotional'
    elif has_product and not has_person:
        return 'product_display'
    elif has_person and not has_product:
        return 'lifestyle'
    else:
        return 'other'


def run_yolo_pipeline() -> None:
    """
    Run the YOLO object detection pipeline on all images in the data/raw/images directory.

    - Walks through all subdirectories under the image root.
    - Performs object detection on each image.
    - Classifies the image based on detected objects.
    - Saves results to 'yolo_detections.csv' in the raw data directory.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_raw_dir = os.path.abspath(os.path.join(base_dir, os.pardir, 'data', 'raw'))
    image_root = os.path.join(data_raw_dir, 'images')
    output_csv = os.path.join(data_raw_dir, 'yolo_detections.csv')

    if not os.path.exists(image_root):
        logging.error(f"Image root directory not found at {image_root}")
        return

    results_list: List[Dict[str, str]] = []

    logging.info(f"Starting YOLO pipeline on images in {image_root}...")
    
    for root, _, files in os.walk(image_root):
        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(root, filename)
                logging.info(f"Processing image: {image_path}")

                # Perform inference
                results = model(image_path)

                detected_in_image: List[str] = []
                max_conf = 0.0

                for result in results:
                    for box in result.boxes:
                        label = result.names[int(box.cls)]
                        conf = float(box.conf)
                        detected_in_image.append(label)
                        if conf > max_conf:
                            max_conf = conf

                category = classify_image(set(detected_in_image))

                # Capture channel name from folder and message ID from filename
                channel_name = os.path.basename(root)
                msg_id = filename.split('_')[0]

                results_list.append({
                    'message_id': msg_id,
                    'channel': channel_name,
                    'image_name': filename,
                    'detected_objects': ", ".join(detected_in_image),
                    'confidence_score': round(max_conf, 4),
                    'image_category': category
                })

    # Save results to CSV
    df = pd.DataFrame(results_list)
    df.to_csv(output_csv, index=False)
    logging.info(f"Processing finished. Results saved to: {output_csv}")


if __name__ == "__main__":
    run_yolo_pipeline()
