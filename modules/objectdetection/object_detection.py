import cv2
import numpy as np

def get_output_layers(net):

    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1]
                     for i in net.getUnconnectedOutLayers()]

    return output_layers


def draw_prediction(
        img,
        class_id,
        classes,
        confidence,
        x,
        y,
        x_plus_w,
        y_plus_h,
        colors):

    label = str(classes[class_id]) + str(format(confidence * 100, '.2f')) + '%'
    color = colors[class_id]

    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
    cv2.putText(img, label, (x - 10, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


def draw_bounding_boxes(
        image,
        boxes,
        indices,
        class_ids,
        classes,
        confidences,
        colors):
    for i in indices:
        i = i[0]
        box = boxes[i]
        x = box[0]
        y = box[1]
        w = box[2]
        h = box[3]

        draw_prediction(
            image,
            class_ids[i],
            classes,
            confidences[i],
            round(x),
            round(y),
            round(
                x + w),
            round(
                y + h),
            colors)


def keep_relevant_predictions(outs, width, height):
    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = center_x - w / 2
                y = center_y - h / 2
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])

    return boxes, confidences, class_ids


def object_detection(image, classes, model_weight_path, model_conf_path):

    net = cv2.dnn.readNetFromDarknet(model_conf_path, model_weight_path)

    # prepare model
    scale = 0.00392
    blob = cv2.dnn.blobFromImage(
        image, scale, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)

    # Apply model
    outs = net.forward(get_output_layers(net))

    # Keep relevant predictions
    boxes, confidences, class_ids = keep_relevant_predictions(
        outs=outs, width=image.shape[1], height=image.shape[0])

    # Apply NMS
    conf_threshold = 0.5
    nms_threshold = 0.4
    indices = cv2.dnn.NMSBoxes(
        boxes,
        confidences,
        conf_threshold,
        nms_threshold)

    # Draw Bounding Box
    colors = np.random.uniform(0, 255, size=(len(classes), 3))
    draw_bounding_boxes(
        image,
        boxes,
        indices,
        class_ids,
        classes,
        confidences,
        colors)
