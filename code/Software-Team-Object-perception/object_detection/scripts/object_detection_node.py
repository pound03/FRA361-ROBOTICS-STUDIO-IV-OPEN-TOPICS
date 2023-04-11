#!/usr/bin/env python3

from cv_bridge import CvBridge  # Package to convert between ROS and OpenCV Images.
import cv2                      # OpenCV library.
import torch
import numpy as np
import pandas as pd

import rclpy
from rclpy.node import Node
    # Import Massages.
from std_msgs.msg import Int8
from sensor_msgs.msg import Image
from geometry_msgs.msg import Point32
from std_msgs.msg import String
    # Import Services.
from std_srvs.srv import Empty as Empty_srv
# from ability_behavior_object.srv import CallPosition, CallColor

class Object_Recognition(Node):
    def __init__(self):
        super().__init__('object_recognition')
            # Create service to enable this node to detecting.
        # Command: ros2 service call /Object_Recognition/enable std_srvs/srv/Empty
        self.enble_service = self.create_service(Empty_srv,'/Object_Recognition/enable',self.enable_callback)
        self.isEnable = False
        
        rate = 10
        self.timer = self.create_timer(1/rate,self.timer_callback)

        self.topic_publisher = self.create_publisher(Int8,'/Object_Recognition/detection_status',10)
            # Initial running status.
        self.param_status = Int8()
        self.param_status.data = 0

        # -------------------------------------------------------------------------------------------------------------
        print('Object ability node activate')
            # Load model from path (path reference from where we run command. In this case we run node at workspace).
        self.model = torch.load('src/Software-Team/object_detection/src/model/yolov5_small_local.pt')
        # self.model = torch.load('src/object_detection/src/model/yolov5_small_local.pt')
        self.model = self.model.eval()
            # Used to convert between ROS and OpenCV images.
        self.br = CvBridge()
            # Initial variables.
        self.current_frame = np.zeros((480,640,3))                      # Frame for detect and display.
        self.target = ['backpack', 'handbag', 'suitcase']               # Target tpye that can be change from service in the future.
        self.Target_Position = Point32()                                # Target position output.
        self.Target_Position.x = 0.0
        self.Target_Position.y = 0.0
        self.Target_Position.z = 0.0
        self.Target_Color = String()                                    # Target color output.
        self.count = 0
        self.count2 = 0
        self.get_camera_info_check = 0                                  # Check that system get CameraInfo or not.
        self.rs2_position_x = 0                                         # Initial value position for subscibe value from estimate_coordinate node.
        self.rs2_position_y = 0

        self.Image_subscription = self.create_subscription(             # Subscribe Image massage through topic '/camera/color/image_raw'.
            Image,                                                      # This will use for Object detection.
            '/camera/color/image_raw', 
            self.Image_listener_callback, 
            10)
        self.Image_subscription                                         # prevent unused variable warning.

        self.Depth_Image_subscription = self.create_subscription(       # Subscribe Image massage through topic '/camera/depth/image_rect_raw'.
            Image,                                                      # This will use for estimate depth.
            '/camera/depth/image_rect_raw', 
            self.Depth_Image_listener_callback, 
            10)
        self.Depth_Image_subscription                                   # prevent unused variable warning.
        
        self.Position_rs2_subscription = self.create_subscription(      # Subscribe Point32 massage through topic 'position_from_rs2'.
            Point32,                                                    # Get position (x, y, z) in real world coordinate from estimate_coordinate node.
            'position_from_rs2', 
            self.Position_rs2_subscription_callback, 
            10)
        self.Position_rs2_subscription                                  # prevent unused variable warning.

            # Create the publisher. This publisher will publish target_position (xyz [float32]) through topic 'target_position'.
        self.target_position_publisher = self.create_publisher(Point32, 'target_position', 10)
            # Create the publisher. This publisher will publish target_color (color name [string]) through topic 'target_color'.
        self.target_color_publisher = self.create_publisher(String, 'target_color', 10)

        self.position_to_rs2_publisher = self.create_publisher(Point32, 'position_for_estimate_coordinate', 10)

            # Create service. These service will call target position and target color.
        # Command: ros2 service call /get_position ability_behavior_object/srv/CallPosition
        # self.get_position_service = self.create_service(CallPosition,'/get_position',self.get_position_srv_callback)
        # Command: ros2 service call /get_color ability_behavior_object/srv/CallColor
        # self.get_color_service = self.create_service(CallColor,'/get_color',self.get_color_srv_callback)

    def timer_callback(self):
        if self.isEnable:
            self.ability_action()
        # else:
            # cv2.destroyAllWindows()                         # close displaying.
        self.topic_publisher.publish(self.param_status)     # Return working status.

    def enable_callback(self,request,response):             # Enable this node to detecting.
        self.isEnable = True
        return response

    def ability_action(self):
        self.param_status.data = 0                          # Status = RUNNING.
        
        results = self.model(self.current_frame)            # result from model yolov5.
        cv2.imshow('yolo',np.squeeze(results.render()))     # Display image.
        cv2.waitKey(1)                                      # keep frame display.

            # Get result in the form of pandas dataframe and addition feature columns.
        self.df = self.results_addition(results.pandas().xyxy[0], self.current_frame, self.target)

            # Condition for detecting:
        # confidence must be >= 0.2.
        if self.df.shape[0] != 0 and self.df[self.df['confidence'] >= 0.2].shape[0] >= 1 and self.df[self.df['z_pose'] != 0.0].shape[0] >= 1:
            self.count += 1
            # print(self.count)
            
        # and must be continue detected by around 2 seconds.
        else:
            self.count2 += 1
            if self.count2 >= 8:
                self.count = 0
                self.count2 = 0
                # print(self.count)

            # Display result form detection in the form of pandas dataframe.
        print(self.df)

            # If an object is continue detected for 10 frames.
        if self.count >= 10:
            self.Position_to_rs2_publish(                                       # Publish pixel position (x, y) and depth to estimate_coordinate_node. 
                                        x_pix = self.df.at[0,'x_mid'], 
                                        y_pix = self.df.at[0,'y_mid'], 
                                        z = self.df.at[0,'z_pose'])
            self.count = 0                                                      # Reset condition value for prepare next detection.
            self.count2 = 0
            self.isEnable = False                                               # Note stop detecting.    

    def Image_listener_callback(self, data):
        self.current_frame = self.br.imgmsg_to_cv2(data)                            # Convert ROS Image message to OpenCV image.
        self.current_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)    # Convert BGR colors to RGB colors.

    def Depth_Image_listener_callback(self, msg:Image):
        self.depth_frame = self.br.imgmsg_to_cv2(msg)                               # Convert ROS Image message to OpenCV image.

    def Position_rs2_subscription_callback(self, msg:Point32):
        self.rs2_position_x = msg.x
        self.rs2_position_y = msg.y
        # print(self.rs2_position_x, self.rs2_position_y)
        # print('********************')
        self.df.at[0,'x_pose'] = self.rs2_position_x                        # Get real-world postion (x,y).
        self.df.at[0,'y_pose'] = self.rs2_position_y
        print(self.df)
        self.update()                                                       # Update value to system.
        self.target_color_publisher.publish(self.Target_Color)              # Publish target color.
        self.target_position_publisher.publish(self.Target_Position)        # Publish target postion.
        print('-----------------------')
        print(self.Target_Color.data)                                       # Display target color and target position values.
        print(self.Target_Position)
        self.param_status.data = 1                                          # Status = SUCCESS.

    # def get_position_srv_callback(self,request:CallPosition.Request, response:CallPosition.Response):
    #     self.update()                                                       # Update value to system.
    #     self.target_position_publisher.publish(self.Target_Position)        # Publish target postion.
    #     response.position.x = self.Target_Position.x
    #     response.position.y = self.Target_Position.y
    #     response.position.z = self.Target_Position.z
    #     return response                                                     # Return response (Target position).

    # def get_color_srv_callback(self,request:CallColor.Request, response:CallColor.Response):
    #     self.update()                                                       # Update value to system.
    #     self.target_color_publisher.publish(self.Target_Color)              # Publish target color.
    #     response.color.data = self.Target_Color.data
    #     return response                                                     # Return response (Target color).

    def update(self):
        if self.df.empty == False:                                          # If model can detect at least 1 object.
            self.Target_Position.x = self.df.at[0,'x_pose']                 # Update x, y ,z and color of target to system.
            self.Target_Position.y = self.df.at[0,'y_pose']
            self.Target_Position.z = self.df.at[0,'z_pose']
            self.Target_Color.data = self.df.at[0,'color']
        else:                                                               # If can't detect anything.
            self.Target_Position.x = 0.0                                    # Update x, y ,z and color of target to system with default values.
            self.Target_Position.y = 0.0
            self.Target_Position.z = 0.0
            self.Target_Color.data = 'undifined'

    def results_addition(self,df,frame,target):
            # Addintion features [x_mid, y_mid, color, x_pose, y_pose and z_pose].
        addition = pd.DataFrame({'x_mid':[0.0], 'y_mid':[0.0], 'color':['undefined'], 'x_pose':[0.0], 'y_pose':[0.0], 'z_pose':[0.0]})

        if df.empty == 0:                                                                           # If model detect something.
            df = pd.concat([df,addition],axis=1)
            for i in range(df.shape[0]):                                                            # For loop for each object that has been detect.
                df.at[i,'x_mid'] = (df.at[i,'xmax'] - df.at[i,'xmin'])/2.0 + df.at[i,'xmin']        # Get pixel postion of middle object.
                df.at[i,'y_mid'] = (df.at[i,'ymax'] - df.at[i,'ymin'])/2.0 + df.at[i,'ymin']
                df.at[i,'color'] = self.color_detection(frame, round(df.at[i,'x_mid']), round(df.at[i,'y_mid']))    # Get color of middle of object.
                df.at[i,'z_pose'] = self.depth_frame[round(df.at[i,'y_mid']), round(df.at[i,'x_mid'])]              # Get depth of middle of object.
        else:
            df = pd.concat([df,addition],axis=1)

        df_target = df[(df['name'] == target[0]) | (df['name'] == target[1]) | (df['name'] == target[2])]           # Select targets object.
        df_target = df_target.reset_index(drop=True)
        return df_target

    def Position_to_rs2_publish(self, x_pix, y_pix, z):         # Function for publish pixel position (x, y) and depth to stimate_coordinate_node.
        msg = Point32()                                         # Through message type Point32.
        msg.x = x_pix
        msg.y = y_pix
        msg.z = z
        self.position_to_rs2_publisher.publish(msg)

    def color_detection(self,frame,x,y):                        # Color detection function.

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)      # convert BGR frame to HSV frame.
        pixel_center = hsv_frame[y,x]                           # Set the pixel to be detected.

        H_value = pixel_center[0] * 360.0 / 179.0               # convert range from 0-179 to 0-360
        S_value = pixel_center[1] * 100.0 / 255.0               # convert range from 0-255 to 0-100
        V_value = pixel_center[2] * 100.0 / 255.0               # convert range from 0-255 to 0-100

            # Color Condition
        if V_value <= 30:
            color = 'black'
        elif S_value <= 20.0:
            if V_value <= 60:
                color = 'gray'
            else:
                color = 'white'
        else:    
            if H_value <= 15.0:
                color = 'red'
            elif H_value <= 35.0:
                color = 'orange'
            elif H_value <= 65.0:
                color = 'yellow'
            elif H_value <= 160.0:
                color = 'green'
            elif H_value <= 205.0:
                color = 'cyan'
            elif H_value <= 280.0:
                color = 'blue'
            elif H_value <= 300.0:
                color = 'purple'
            elif H_value <= 340.0:
                color = 'pink'
            else:
                color = 'red'
        return color

def main(args=None):
    rclpy.init(args=args)
    object_rocognition = Object_Recognition()
    rclpy.spin(object_rocognition)
    object_rocognition.destroy_node()
    object_rocognition.shutdown()
    rclpy.shutdown()

if __name__=='__main__':
    main()
