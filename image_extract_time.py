#!/usr/bin/env python

# Copyright 2017 Cheng Huimin

"""Extract images from a rosbag, at specific timing(s)
"""

import os
import argparse

import cv2

import rosbag
import rospy

import yaml

import shutil

import csv

from cv_bridge import CvBridge
#from sensor_msgs.msg import Image

def main():
    """Extract images from a rosbag, at specific timing(s)
    """
    parser = argparse.ArgumentParser(description="Extract images from a rosbag, at specific timing(s)")
    parser.add_argument("bag_file", help="Input ROS bag.")
    parser.add_argument("output_dir", help="Output directory.")
    parser.add_argument("left",help="Left Image topic.")
    parser.add_argument("right",help="Right Image topic.")
    parser.add_argument("-l", action="append",help="add additional message log to csv")
    parser.add_argument("-t", action="append",help="millisecond of the image to be extracted",type=int)

    args = parser.parse_args()

    print "Extract images from %s on left=%s and right=%s into %s" % (args.bag_file,args.left,args.right, args.output_dir)

    bag = rosbag.Bag(args.bag_file, "r")
    info = yaml.load(bag._get_yaml_info())
    #print "start=",info['start'] ," end=", info['end'], " duration=" , info['duration']
    bridge = CvBridge()
    
    bag_start = rospy.Time().from_sec(float(info['start']))

    if os.path.exists(args.output_dir): shutil.rmtree(args.output_dir)
    os.mkdir(args.output_dir)

    count = 0
    if not args.t:
        print "Error: At least 1 -t is needed"
        return -1

    # convertin argument into Time variables
    tlist = [rospy.Duration().from_sec(ti / 1e3) for ti in args.t]

    #extracting images in 1 pass
    for ti in tlist:
        #print "Extracting Image at %.2fs" % (ti.to_nsec()/1e9)
        for topicstr in [args.left , args.right]:
            ptr = bag.read_messages(topics=topicstr,start_time=bag_start + ti)
        
            topic, msg, t = next(ptr)
            print topic, " at ", (t-bag_start).to_sec()
            cv_img = bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
            cv2.imwrite(os.path.join(args.output_dir, "%08i%s.png" % ((t-bag_start).to_sec()*1e3,topic.replace('/','_'))), cv_img)

    
    #extracting other messages
    for li in args.l or []:
        #with open(os.path.join(args.output_dir,"%s.csv" % topic.replace('/','_')),'w') as outcsv:
            #writer = csv.writer(outcsv)
            for ti in tlist:
                #print "Extracting %s at %.2fs" % (li,ti.to_nsec()/1e9)
                ptr = bag.read_messages(topics=[li],start_time=bag_start + ti)
                try:
                    topic, msg, t = next(ptr)
                except StopIteration:
                    print "WARNING: Could not find %s from time %.2fs" % (li,ti.to_nsec()/1e9)
                    continue
                print topic, " at ", (t-bag_start).to_sec()
                fd = open(os.path.join(args.output_dir,"%08i%s.txt" % (((t-bag_start).to_sec()*1e3),topic.replace('/','_'))),'w')
                fd.write("%s\n" % msg)
                #writer.writerow([(t-bag_start).to_sec(),msg])

            
                

    return
if __name__ == '__main__':
    main()