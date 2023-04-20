model = torch.load('object/scripts/yolov7.pt', map_location=torch.device('cpu'))['model'].float().fuse().eval()
# # Make predictions using YOLOv5 model
# predictions = model(tensor)

# # Print predicted labels and bounding boxes
# print(predictions.pandas().xyxy[0])