import cv2
import numpy as np
import time

# --- Real-Time Object Detection & Billing System ---
thres = 0.45  # Confidence threshold
nms_threshold = 0.2
cap = cv2.VideoCapture(0)

# Load class names from coco.names file
classNames = []
classFile = r'C:\Users\analo\object detection model\coco.names'  # Ensure this path is correct
with open(classFile, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

# Define objects of interest and prices
items_of_interest = {"bottle", "book", "toothbrush"}
items_prices = {"bottle": 5, "book": 10, "toothbrush": 3}

# Tracking detected items
detected_items = {}  # Stores item counts
seen_items = set()   # Ensures each item is counted only once
last_detected_item = None  # Tracks the last detected item

# Load model files (Ensure these paths are correct)
weightsPath = r'C:\Users\analo\object detection model\frozen_inference_graph.pb'
configPath = r'C:\Users\analo\object detection model\ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'

# Load the pre-trained model
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Initialize FPS counter
prev_time = 0

while True:
    success, img = cap.read()
    if not success:
        break

    # Detect objects
    classIds, confs, bbox = net.detect(img, confThreshold=thres)

    if classIds is not None:
        if isinstance(classIds, np.ndarray) and len(classIds) > 0:
            indices = cv2.dnn.NMSBoxes(bbox, confs, thres, nms_threshold)

            if len(indices) > 0:
                indices = indices.flatten()  # Flatten indices array

                for i in indices:
                    classId = int(classIds[i]) if isinstance(classIds, np.ndarray) else int(classIds)
                    confidence = float(confs[i]) if isinstance(confs, np.ndarray) else float(confs)
                    box = bbox[i]

                    class_name = classNames[classId - 1].lower()

                    if class_name in items_of_interest and confidence > thres:
                        # Draw bounding box and label
                        cv2.rectangle(img, box, (0, 255, 0), 2)
                        cv2.putText(img, f"{class_name.upper()} ({confidence:.2f})",
                                   (box[0] + 10, box[1] + 30),
                                   cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 0), 2)

                        # **Prevent Multiple Counting**
                        if class_name not in seen_items:
                            detected_items[class_name] = detected_items.get(class_name, 0) + 1
                            seen_items.add(class_name)  # Mark as counted
                            last_detected_item = class_name  # Store last detected item

    # Create invoice panel
    height, width = img.shape[:2]
    panel_width = 320
    white_panel = np.ones((height, panel_width, 3), dtype=np.uint8) * 255

    # Invoice Header
    cv2.putText(white_panel, "Invoice", (100, 40),
               cv2.FONT_HERSHEY_TRIPLEX, 0.8, (0, 0, 255), 2)

    # Display detected items and prices
    y_position = 80
    total = 0
    for item, count in detected_items.items():
        price = items_prices[item]
        item_total = price * count
        total += item_total
        cv2.putText(white_panel, f"{item}: {count} x ${price} = ${item_total}",
                   (20, y_position), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        y_position += 30

    # Display total cost
    cv2.putText(white_panel, f"Total: ${total}", (20, height - 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    # FPS Counter
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
    prev_time = curr_time
    cv2.putText(img, f"FPS: {int(fps)}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    # Combine main frame and invoice panel
    combined = np.hstack((img, white_panel))
    cv2.imshow("Object Detection & Billing System", combined)

    # Handle key presses
    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    elif key == ord('c'):  # Reset counts
        detected_items.clear()
        seen_items.clear()  # Reset seen items as well
        last_detected_item = None
    elif key == 13:  # Enter key to increase quantity
        if last_detected_item:
            detected_items[last_detected_item] += 1
    elif key == ord('s'):  # Save invoice to file
        with open("invoice.txt", "w") as f:
            f.write("Invoice\n")
            f.write("="*20 + "\n")
            for item, count in detected_items.items():
                price = items_prices[item]
                item_total = price * count
                f.write(f"{item}: {count} x ${price} = ${item_total}\n")
            f.write("="*20 + f"\nTotal: ${total}\n")
        print("Invoice saved as 'invoice.txt'")

cap.release()
cv2.destroyAllWindows()






