#!/usr/bin/env python

import rospy
import os
import numpy as np
import numpy.linalg as lin
import kalman_filter
import math
import cv2
import pandas as pd


from sensor_msgs.msg import Image
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge
from yolov5_ros.msg import BoundingBoxes
from yolov5_ros.msg import BoundingBox
from yolov5_ros.msg import RadarObjectList
from filterpy.kalman import KalmanFilter
from time import time

class fusion():
    def __init__(self):
        
        self.bridge = CvBridge()
        self.fusion_index_list = []
        self.fusion_distance_list = []
        self.radar_object_list = []
        self.bounding_box_list = []
        self.distance_thresh = 6
        self.angle_thresh = 30
        self.my_speed = 20
        self.flag = 0

        rospy.init_node('fusion_node', anonymous=False)
        print(rospy.get_time())
        rospy.Subscriber('yolov5/detections', BoundingBoxes, self.camera_object_callback)
        rospy.Subscriber('radar_objects', RadarObjectList, self.radar_object_callback)
        rospy.Subscriber('/yolov5/image_out', Image, self.visualize)

    # 카메라 Bounding Box Callback 함수
    def camera_object_callback(self, data):
        if self.flag == 0:
            self.init_time = time()
        self.bounding_box_list = data.bounding_boxes
        self.flag += 1
        # rospy.Subscriber('radar_objects', RadarObjectList, self.radar_object_callback)

    # 레이더 XYZV Callback 함수
    def radar_object_callback(self, data):
        self.radar_object_list = data.RadarObjectList
    
    # 레이더 2D point가 Bounding Box 내에 위치하는지 return (True or False)
    def is_in_bbox(self, bbox, radar_2d):

        if radar_2d[0] > bbox.xmin and radar_2d[0] < bbox.xmax and radar_2d[1] > bbox.ymin and radar_2d[1] < bbox.ymax:
            return True
        
        else:
            return False
    
    # 3D point -> 2D point Projection
    def transform(self, radar_object):
        intrinsic_matrix = np.array([[640/math.tan(0.5*math.radians(50)), 0, 640], [0, 640/math.tan(0.5*math.radians(50)), 480], [0, 0, 1]])
        projection_matrix = np.array([[0.1736, -0.9848, 0, 1.3842], [0, 0, -1, 0.5], [0.9848, 0.1736, 0, 2.0914]])
        
        world_point = np.array([[radar_object.x], [radar_object.y], [radar_object.z], [1]])

        transformed_matrix = intrinsic_matrix @ projection_matrix @ world_point

        scaling = transformed_matrix[2][0]

        transformed_matrix /= scaling

        x = round(transformed_matrix[0][0])
        y = round(transformed_matrix[1][0])

        return (x,y)
            

    # Bounding Box 밑변 중점 Z=-0.5 가정하고 2D point -> 3D point Projection
    def transformation_demo(self):
        Rt = np.array([[0.1736, -0.9848, 0], [0, 0, -1], [0.9848, 0.1736, 0]]).T
        
        # YOLO detecting 될 때
        if len(self.bounding_box_list) != 0:
            for bbox in self.bounding_box_list:

                x = (bbox.xmin + bbox.xmax) / 2
                y = bbox.ymax

                fx = 640/math.tan(math.radians(25))
                fy = fx

                u = (x - 640) / fx
                v = (y - 480) / fy

                Pc = np.array([[u], [v], [1]])

                t = np.array([[1.3842], [0.5], [2.0914]])

                pw = Rt @ (Pc-t)
                cw = Rt @ (-t)

                k = (cw[2][0] + 0.5) / (cw[2][0] - pw[2][0])

                world_point = cw + k*(pw-cw)
                
                x_c = world_point[0][0]
                y_c = world_point[1][0]

                camera_object = (x_c, y_c)

                self.matching(bbox, camera_object)

        # YOLO detecting 끊겼을 때 (radar_risk_calculate 함수 호출)
        else:
            min_x = math.inf
            for radar_object in self.radar_object_list:
                if radar_object.x < min_x:
                    min_x = radar_object.x
            
            self.radar_risk_calculate(min_x)
            
    # 동일 객체 판단 및 최종 거리, 속도 데이터 산출
    def matching(self, bbox, camera_object):
        # 1단계 통과한 레이더 3D point List
        self.filtered_radar_object_list = []
        
        # X 좌표 List
        self.x_list = []

        # 레이더 데이터 있을 때
        if len(self.radar_object_list) != 0:
            for radar_object in self.radar_object_list:
                # Bounding Box 내에 위치하는 3D 레이더 포인트 필터링
                if self.is_in_bbox(bbox, self.transform(radar_object)) == True:
                    self.filtered_radar_object_list.append(radar_object)
                    self.x_list.append(radar_object.x)
        
        min_iou = math.inf
        min_x = math.inf
        min_idx = -1
        cnt = 0
        
        if len(fusion_distance_list) != 0:
            # 1단계 거친 레이더 포인트 남아있을 때
            if len(self.filtered_radar_object_list) != 0:
                for radar_object in self.filtered_radar_object_list:
                    if fusion_distance_list[-1] < 15:
                        # print("Fucking : ", abs(only_radar_distance_list[-1] - radar_object.x))
                        print("Last X : ", only_radar_distance_list[-1])
                        print("Cur X : ", radar_object.x)
                        print("Difference : ", abs(only_radar_distance_list[-1] - radar_object.x))
                        if abs(only_radar_distance_list[-1] - radar_object.x) < 0.35:
                                    
                            if math.sqrt((radar_object.x - camera_object[0])**2 + (radar_object.y - camera_object[1])**2) < min_iou:
                                min_idx = cnt
                                min_iou = math.sqrt((radar_object.x - camera_object[0])**2 + (radar_object.y - camera_object[1])**2)
                            
                        else:
                            pass
                    
                    else:
                         if math.sqrt((radar_object.x - camera_object[0])**2 + (radar_object.y - camera_object[1])**2) < min_iou:
                            min_idx = cnt
                            min_iou = math.sqrt((radar_object.x - camera_object[0])**2 + (radar_object.y - camera_object[1])**2)

                    cnt += 1

                if min_idx < 0:
                    final_distance = fusion_distance_list[-1]
                    final_velocity = velocity_list[-1]
                    # print("###Filter Succeed###")
                
                else:
                    final_distance = (camera_object[0]*0.3 + self.filtered_radar_object_list[min_idx].x*0.7)
                    print("Selected Radar X : ", self.filtered_radar_object_list[min_idx].x)
                    final_velocity = self.filtered_radar_object_list[min_idx].velocity

                if abs(final_velocity - velocity_list[-1]) > 1:
                    final_velocity = velocity_list[-1]


                # print("!!!!Min Index!!!! : ", min_idx)
                # print("Last Point : ", only_radar_distance_list[-1])
                # print("Min Point : ", self.filtered_radar_object_list[min_idx].x)
                # print("Difference : ", abs(only_radar_distance_list[-1] - self.filtered_radar_object_list[min_idx].x))

                cv2.line(self.image, self.transform(self.filtered_radar_object_list[min_idx]), self.transform(self.filtered_radar_object_list[min_idx]), (0, 255, 0), 15)

            # 레이더 포인트 없을 때
            else:
                final_distance = fusion_distance_list[-1]
                final_velocity = velocity_list[-1]
        
        # 첫 번째 루프
        else:
            # 1단계 거친 레이더 포인트 남아있을 때
            if len(self.filtered_radar_object_list) != 0:
                for radar_object in self.filtered_radar_object_list:
                    if math.sqrt((radar_object.x - camera_object[0])**2 + (radar_object.y - camera_object[1])**2) < min_iou:
                        min_idx = cnt
                        min_iou = math.sqrt((radar_object.x - camera_object[0])**2 + (radar_object.y - camera_object[1])**2)

                    cnt += 1
                cv2.line(self.image, self.transform(self.filtered_radar_object_list[min_idx]), self.transform(self.filtered_radar_object_list[min_idx]), (0, 255, 0), 15)
            
                final_distance = (camera_object[0]*0.3 + self.filtered_radar_object_list[min_idx].x*0.7)
                
                final_velocity = self.filtered_radar_object_list[min_idx].velocity

            # 1단계 거친 레이더 포인트 없을 때
            else:
                final_distance = camera_object[0]
                final_velocity = velocity_list[-1]
        
        # 속도 2번째 이후 loop
        if len(velocity_list) != 0:
            # print("Initial : ", velocity_list[-1])
            kalman_velocity = kalman_filter.call_1dkalman(kf, velocity_list[-1], final_velocity)
        
        # 속도 1번째 loop
        else:
            kalman_velocity = final_velocity

        x_list = []
        d_min = math.inf
        sum = 0
        total_num = len(self.radar_object_list)
            
        for radar_object in self.radar_object_list:
            x_list.append(radar_object.x)
            if len(only_radar_distance_list) != 0:
                if abs(radar_object.x - only_radar_distance_list[-1]) < d_min:
                    d_min = abs(radar_object.x - only_radar_distance_list[-1])
            sum += radar_object.x
        
        average = float(sum / total_num)
        if total_num == 0:
            only_radar_distance_list.append(only_radar_distance_list[-1])
        else:
            if d_min < 1 or d_min == math.inf:
                only_radar_distance_list.append(min(x_list))
            else:
                only_radar_distance_list.append(only_radar_distance_list[-1])
        
        print("Final distance : ", final_distance)

        only_camera_distance_list.append(camera_object[0])
        
        fusion_distance_list.append(final_distance)
        
        now = rospy.get_rostime()
        rospy.loginfo("Time : %i", now.secs)
        cur = time()
        velocity_list.append(kalman_velocity)
        
        time_list.append(cur - self.init_time)

        self.risk_calculate(final_distance, kalman_velocity * 3.6)


    def risk_calculate(self, distance, velocity):
        
        if distance < 7:
            cv2.rectangle(self.image, (0, 0), (1280, 960), (0,0,255), 50, 1)
        
        else:
            car_velocity = self.my_speed - velocity

            crash_time = distance * 3600 / (1000 * (car_velocity - math.sin(math.radians(85))*self.my_speed))

            crash_list.append(crash_time)
            
            lane_change_time = 3.5 * 3600 / (1000*self.my_speed * math.cos(math.radians(85)))
            
            # Ok to change lane
            if crash_time - lane_change_time >= 3.5 or self.my_speed > car_velocity:
                pass
            
            # Warning
            elif crash_time - lane_change_time < 3.5 and crash_time - lane_change_time >= 2.5:
                cv2.rectangle(self.image, (0, 0), (1280, 960), (0,130,255), 50, 1)
                cv2.line(self.image, (390, 745), (int((self.bounding_box_list[-1].xmin + self.bounding_box_list[-1].xmax)/2), self.bounding_box_list[-1].ymax), (0, 130, 255), 5, 1)
                cv2.line(self.image, (240, 745), (540, 745), (0, 130, 255), 5, 1)
                cv2.line(self.image, (self.bounding_box_list[-1].xmin, self.bounding_box_list[-1].ymax), (self.bounding_box_list[-1].xmax, self.bounding_box_list[-1].ymax), (0, 130, 255), 5, 1)

            # Dangerous
            else:
                cv2.rectangle(self.image, (0, 0), (1280, 960), (0,0,255), 50, 1)
                cv2.line(self.image, (390, 745), (int((self.bounding_box_list[-1].xmin + self.bounding_box_list[-1].xmax)/2), self.bounding_box_list[-1].ymax), (0, 0, 255), 5, 1)
                cv2.line(self.image, (240, 745), (540, 745), (0, 0, 255), 5, 1)
                cv2.line(self.image, (self.bounding_box_list[-1].xmin, self.bounding_box_list[-1].ymax), (self.bounding_box_list[-1].xmax, self.bounding_box_list[-1].ymax), (0, 0, 255), 5, 1)
    
    # 카메라 detecting 안될 때 레이더 데이터로만 경고
    def radar_risk_calculate(self, distance):

        if distance < 7:
            cv2.rectangle(self.image, (0, 0), (1280, 960), (0,0,255), 50, 1)
        
        elif distance < 12:
            cv2.rectangle(self.image, (0, 0), (1280, 960), (0,130,255), 50, 1)
        
        else:
            pass
    
    # Image 송출 함수
    def visualize(self, data):

        # self.image = self.bridge.compressed_imgmsg_to_cv2(data, desired_encoding="bgr8")
        self.image = self.bridge.imgmsg_to_cv2(data, desired_encoding="bgr8")
        
        self.transformation_demo()

        cv2.imshow("Display", self.image)
        cv2.waitKey(1)

if __name__ == '__main__':
    
    kf = KalmanFilter(dim_x=2, dim_z=1)

    time_list = []
    only_camera_distance_list = []
    only_radar_distance_list = []
    # fusion_radar_list = []
    fusion_distance_list = []
    velocity_list = []
    crash_list = []

    if not rospy.is_shutdown():
        fusion()
        rospy.spin()
    
    
    # 결과 CSV 파일로 저장
    os.chdir('/home/heven/CoDeep_ws/src/yolov5_ros/src/csv/test')

    df = pd.DataFrame({'Time': time_list, 'Camera': only_camera_distance_list, 'Radar': only_radar_distance_list, 'Fusion': fusion_distance_list})        
    df.to_csv("distance_fusion_test.csv", index=True)

    df2 = pd.DataFrame({'Time': time_list, 'Velocity' : velocity_list})
    df2.to_csv("velocity_fusion_test.csv", index=False)

    # df3 = pd.DataFrame({'Crash time' : crash_list})
    # df3.to_csv("crash_fusion_result.csv", index=False)

    # df4 = pd.DataFrame({'Radar': only_radar_distance_list})
    # df4.to_csv("only_radar_distance.csv", index=False)
