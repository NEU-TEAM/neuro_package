#!/usr/bin/env python

"""
    moveit_ik_demo.py - Version 0.1 2014-01-14
    
    Use inverse kinemtatics to move the end effector to a specified pose
    
    Created for the Pi Robot Project: http://www.pirobot.org
    Copyleft (c) 2014 Patrick Goebel.  All lefts reserved.

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.5
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details at:
    
    http://www.gnu.org/licenses/gpl.html
"""

import rospy
import sys
import moveit_commander

from std_msgs.msg import Bool
from std_msgs.msg import Int32
from geometry_msgs.msg import PoseStamped

left_gripper_open = [1.57]
left_gripper_close = [0]

# Initialize the move_group API
moveit_commander.roscpp_initialize(sys.argv)

# Initialize the move group for the left arm
left_arm = moveit_commander.MoveGroupCommander('left_arm')
left_gripper = moveit_commander.MoveGroupCommander('left_gripper')

# Set the reference frame for pose targets
reference_frame = 'base_footprint'
# Set the left arm reference frame accordingly
left_arm.set_pose_reference_frame(reference_frame)

# Get the name of the end-effector link
left_eef = left_arm.get_end_effector_link()

# Allow re-planning to increase the odds of a solution
left_arm.allow_replanning(True)

# Allow some leeway in position (meters) and orientation (radians)
left_arm.set_goal_position_tolerance(0.01)
left_arm.set_goal_orientation_tolerance(0.01)


def reset():
    target_pose = PoseStamped()
    target_pose.header.frame_id = reference_frame
    target_pose.header.stamp = rospy.Time.now()

    target_pose.pose.position.x = 0.45
    target_pose.pose.position.y = 0.28
    target_pose.pose.position.z = 1
    target_pose.pose.orientation.x = 0
    target_pose.pose.orientation.y = 0
    target_pose.pose.orientation.z = 0
    target_pose.pose.orientation.w = 1
    # Set the start state to the current state
    left_arm.set_start_state_to_current_state()

    # Set the goal pose of the end effector to the stored pose
    left_arm.set_pose_target(target_pose, left_eef)

    init_positions = [0, 0, 0, 0, 0, 0]
    left_arm.set_joint_value_target(init_positions)
    traj = left_arm.plan()
    left_arm.execute(traj)
    rospy.sleep(1)

    left_gripper.set_joint_value_target(left_gripper_close)
    left_gripper.go()
    rospy.sleep(1)


def move(direction, offset):
    left_arm.shift_pose_target(direction, offset, left_eef)
    left_arm.go()
    rospy.sleep(1)


def gripper_open(status):
    if status:
        left_gripper.set_joint_value_target(left_gripper_open)
    else:
        left_gripper.set_joint_value_target(left_gripper_close)
    left_gripper.go()
    rospy.sleep(1)


def run_fk():
    # Up to down, 6 joints, value range see neurofull_left_ikfast.urdf
    joint_pos_tgt = [0, 0, 0, 0, 1.57, 0]
    left_arm.set_joint_value_target(joint_pos_tgt)
    traj = left_arm.plan()
    left_arm.execute(traj)
    rospy.sleep(1)

    joint_pos_tgt = [-0.4, 0, 0, 1.57, 1.57, 0.4]
    left_arm.set_joint_value_target(joint_pos_tgt)
    traj = left_arm.plan()
    left_arm.execute(traj)
    rospy.sleep(3)

    left_gripper.set_joint_value_target(left_gripper_open)
    left_gripper.go()
    rospy.sleep(1)

    joint_pos_tgt = [0, 0, 0, 1.57, 1.57, 0]
    left_arm.set_joint_value_target(joint_pos_tgt)
    traj = left_arm.plan()
    left_arm.execute(traj)
    rospy.sleep(3)

    joint_pos_tgt = [0.5, 0.1, 0, 0.65, 1.57, 0.4]
    left_arm.set_joint_value_target(joint_pos_tgt)
    traj = left_arm.plan()
    left_arm.execute(traj)
    rospy.sleep(3)

    left_gripper.set_joint_value_target(left_gripper_close)
    left_gripper.go()
    rospy.sleep(1)

    joint_pos_tgt = [0.47, 0, 0, 1.2, 1.57, 0.33]
    left_arm.set_joint_value_target(joint_pos_tgt)
    traj = left_arm.plan()
    left_arm.execute(traj)
    rospy.sleep(0.5)

    joint_pos_tgt = [0, 0, 0, 1.57, 1.57, 0]
    left_arm.set_joint_value_target(joint_pos_tgt)
    traj = left_arm.plan()
    left_arm.execute(traj)
    rospy.sleep(1)


class GraspFK:
    def __init__(self):
        self._planed = False

        # Callbacks for grasp
        self._cb_tgt = rospy.Subscriber('/vision/grasp/pose', PoseStamped, self._target_pose_cb)
        self._cb_result = rospy.Subscriber('/move/grasp/result', Bool, self._target_result_cb)

        # Callback for receiving voice command
        self._cb_reset = rospy.Subscriber('/call/leftarm', Int32, self._voice_cb)
        rospy.loginfo('Left arm: Ready for forward kinetic.')

    def _target_pose_cb(self, pose):
        if not self._planed:
            run_fk()
            self._planed = True

    def _target_result_cb(self, data):
        # If result returns true, which means the plan has been finished, reset.
        if data.data:
            self._planed = False

    def _voice_cb(self, data):
        if data.data == 1:
            reset()
            self._planed = False
        elif data.data == 2:
            gripper_open(True)
        elif data.data == 3:
            move(0, 0.05)
        elif data.data == 4:
            move(0, -0.05)
        elif data.data == 5:
            move(1, 0.05)
        elif data.data == 6:
            move(1, -0.05)
        else:
            rospy.logwarn('Left arm: Unknown voice command.')


class NodeMain:
    def __init__(self):
        rospy.init_node('neurobot_arm_left', anonymous=False)
        rospy.on_shutdown(self.shutdown)
        fk = GraspFK()
        rospy.spin()

    @staticmethod
    def shutdown():
        rospy.loginfo("Left arm: Shutting down")

if __name__ == "__main__":
    try:
        NodeMain()
    except rospy.ROSInterruptException:
        rospy.loginfo("Left arm: Terminated")
