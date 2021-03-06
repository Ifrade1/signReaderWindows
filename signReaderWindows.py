################################################################################
# Copyright (C) 2012-2013 Leap Motion, Inc. All rights reserved.               #
# Leap Motion proprietary and confidential. Not for distribution.              #
# Use subject to the terms of the Leap Motion SDK Agreement available at       #
# https://developer.leapmotion.com/sdk_agreement, or another agreement         #
# between Leap Motion and you, your company or other organization.             #
################################################################################
#
#   written by Sarah Almeda at The College of New Jersey 9/2018

#   written by Sarah Almeda at The College of New Jersey 10/2018
#
#   This code has been modified to run on a windows 64 computer
#   You can find the mac version of the code here:
#   https://github.com/sarah-almeda/signReader
#
#
################################################################################
from __future__ import with_statement
from datetime import timedelta 
import Leap, sys, thread, time,  os, datetime, math 
import getpass, inspect #IL
src_dir = os.path.dirname(inspect.getfile(inspect.currentframe())) #IL
arch_dir = '../lib/x64' if sys.maxsize > 2**32 else '../lib/x86' #IL
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir))) #IL
#termios, tty,
import numpy as np
import numpy.linalg 
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

#margin of error used for comparing distances to detect finger status
thumbExtendedMargin = 70 #if angle between thumb and palm is > this, thumb is extended
thumbUpMargin = 20 #if angle between thumb and hand is < this, thumb is up
thumbInMargin = 10 #if distance from thumb tip to palm is < this, thumb is in
extendedMargin = 9
rollDifference = 25 #if the difference between the roll and 90 is < this, the palm is sideways
thumbStraightMargin = 30
Vmargin = 30 #IL: is this margin, if letter = V?
touchingMargin = 10
isTouchingMargin = 30
straightOutMargin = 10
curledMargin = 10
downMargin = 0
maxFrames = 120      # maximum number of frames to store
maxDistance = 2 # max distance between steady frames

def getSign(fingers, hand, anglesToPalm, fingerAngles, thumbMiddleTouching):
    angleToPalmOf = dict(anglesToPalm) #make a dictionary with angles from fingers to palm
    angleBetween = dict(fingerAngles) #Returns dict with angles in this order: ['TI', 'IM', 'MR', 'RP']
    statusOf = dict(fingers) #make a dictionary with finger initials as keys or 'palm' as key

#    _______
#---'   ____)____   [T] = THUMB
#          ______)  [I] = INDEX FINGER
#          _______) [M] = MIDDLE 
#        _______)   [R] = RING FINGER
#---.__________)    [P] = PINKY

if not (statusOf): #IL: Leap cannot find the hand
        print "I can't see your full hand!"
        return

    ##--------- SIGNS WITH ABNORMAL PALM ORIENTATION ------------###
    if (statusOf['palm'] == 'SIDEWAYS' and statusOf['T'] is 'in' and statusOf['P'] is not 'up'): #G or H
        if (statusOf['M'] == 'up' or statusOf['M'] == 'out'): #IL: if middle finger is up or sticking out
            print "You signed an H"
            return
        else:
            print "You signed a G"
            return
    if (statusOf['palm'] == 'DOWN' and statusOf['P'] is not 'up'): #Q or P
        if (statusOf['M'] == 'up'or statusOf['M'] == 'out'): #IL: if middle finger is up or sticking out
            print "You signed a P"
            return
        else:
            print "You signed a Q"
            return

    ##--------- SIGNS WITH NORMAL PALM ORIENTATION ------------###
    if (statusOf['P'] == 'curled'): #if pinky is curled
        if statusOf['T'] == 'in' and statusOf['I'] is not 'up': #pinky is curled and thumb is in
            print "You signed an E" 
            return
        #if it's not an E, it was probably misread as curled
        for key in statusOf:
            if (statusOf[key] == 'curled'):
                statusOf[key] = 'up'
    
    if(statusOf['P'] == 'down'): #PINKY IS DOWN 
        #CHECK MIDDLE FINGER STATUS
        if (statusOf['M'] == 'down'): #IL:Pointing down?
            if (statusOf['I'] == 'up' and statusOf['T'] == 'up'):
                print "You signed an L"
                return
            elif (statusOf['I'] == 'down' or statusOf['I'] == 'curled'): #all fingers down, curled
                if (statusOf['T'] == 'up' or statusOf['T'] == 'out'): #fingers curled, thumb sticking out
                    print "You signed an A" #or  a T
                    return
                else:
                    print "You signed an S"
                    return
            elif (angleToPalmOf['I'] < 75): #finger is curled
                if (statusOf['palm'] == 'SIDEWAYS'): #Index finger out & curled, hand pointing to the side
                    print "You signed a G"
                    return
                print "You signed an X" #IL: palm is facing up, index is still curled out, rest of fingers in fist
                return
            else:
                print "You signed a D" #palm pointed up, Index finger up, all other fingers curled, touching the thumb
                return
        elif (statusOf['M'] == 'bent' or statusOf['M'] is 'out'):
            if (statusOf['I'] == 'up'):
                print "You signed a K" #IL:Index finger up, middle pointing out, thumb up in between
                return
            if (statusOf['R'] is not 'up'): #IL:humb on pinky, all other fingers curled on top.
                print "You signed an M"
            else:
                print "You signed an N" #IL:thumb resting on top of ring, index and middle resting on thumb
            return
        elif (statusOf['M'] == 'up'):
            if (statusOf['I'] == 'up' ):
                if (angleBetween['IM'] > Vmargin): #IL: Index and middle finger pointed up and out, in V formation
                    print "You signed a V"
                    return
                if (angleBetween['IM'] < touchingMargin):#IL: Index and middle finger up, touching. 
                    print "You signed a U"
                    return
                else:
                    print "You signed an R"#IL: Middle and Index pointed up, interlocked. thumb resting on ring, pinky should be curled down.
                    return
            elif(statusOf['R'] != 'up'): #IL: peace symbol, index and middle finger pointed up and out, everything else curled
                print "Peace among worlds!"
                return
        statusOf['P'] = 'bent'
    if (statusOf['P'] is 'bent' or statusOf['P'] is 'out'): 
        if (statusOf['R'] == 'up' and statusOf['M'] == 'up'): #IL: Middle up, Ring up (and out), pinky bent, Index up (and out)
            print "You signed a W"
            return
        else:
            if (statusOf['I'] == 'up'):
                if (statusOf['T'] == 'out'):
                    if (statusOf['M'] == 'up'):
                        #this person signs U, V, R with their pinky pointed out
                        if (angleBetween['IM'] > Vmargin):
                            print "You signed a V" #IL: Index and middle finger pointed up and out, in V formation
                            return
                        if (angleBetween['IM'] < touchingMargin):
                            print "You signed a U" #IL: Index and middle finger up, touching.
                            return
                        else:
                            print "You signed an R"#IL: Middle and Index pointed up, interlocked. thumb resting on ring, pinky should be curled down.
                            return
                    if (thumbMiddleTouching):
                        print "You signed a D" #IL: thumb and middle touching. Index up. pinky and ring curled out. 
                        return
                    print "You signed an L"
                    return
                elif (statusOf['M'] is 'out' or statusOf['M'] is 'bent'):
                    print "You signed a K" 
                    return
                else:
                    print "You signed a D" #IL: thumb and middle touching. Index up. pinky and ring curled out. 
                    return
            elif (statusOf['M'] != 'up'):
                if (thumbMiddleTouching):
                    print "You signed an O" #IL:thumb and middle touching. all other fingers curled down and out, not touching palm
                else:
                    print "You signed a C" #IL: all fingers curled out, thumb and middle NOT touching.
                return
        statusOf['P'] = 'up'
    if(statusOf['P'] == 'up'):
        if (statusOf['R'] == 'up'): #RING IS EXTENDED
            if (statusOf['I'] == 'up'): #INDEX IS EXTENDED
                     if ((statusOf['T'] is not 'out') and (angleBetween['IM'] <= (touchingMargin+10))): #THUMB IS DOWN AND FINGERS ARE CLOSE
                        print "You signed a B"
                        return
                     else:
                        print "That's an open palm. High five!"
                        return
            else: #INDEX IS NOT EXTENDED
                print "You signed an F" #pinky, ring, & middle up and touching. thumb and index touching.
                return
        else: #RING IS NOT EXTENDED
            if (statusOf['T'] == 'out' ): #THUMB EXTENDED
                if (statusOf['I'] == 'up'): #INDEX IS EXTENDED
                    print "I love you too ;)" #IL: pinky up, index up, thumb pointed up and out. all others curled against palm
                    return
                else:
                    print "You signed a Y" #IL: pinky out sideways, thumb out
                    return
            else:
                print "You signed an I" #IL: pinky up, ring, middle, index curled against palm, thumb resting on top of them.
                return
    print "I don't know what you signed!"

#######################################################################
#
# getFingerStatuses - used to get status of each finger                 #
#   either extended, or bent, and a bent finger can be curled or down   #
#
########################################################################

def getFingerStatuses(fingers, hand, printRequested):
    
    result = []
    status = 'normal'
    fingerAngles = dict(getFingerAngles(fingers, hand, False))
    angleToPalm = dict(anglesToPalm(fingers, hand, False))
    angleToHand = dict(anglesToHand(fingers, hand, False))

    

    #GET PALM STATUS
    roll = (180*(hand.direction.roll)/np.pi)
    if (abs(abs(roll) - 90) < rollDifference):
        status = 'SIDEWAYS'
    if (abs(roll) < rollDifference):
        status = 'DOWN'
    result.append(('palm', status))


    status = 'unknown'
    for a, f in fingers:
        
        ##GET DATA
        shortLength = f.length
        metacarpalLength = (f.bone(0).length/2) #length of half the metacarpal
        fullLength = shortLength + metacarpalLength #estimated length from center of palm to tip of finger
        palmCenter = hand.palm_position
        tipToPalm = abs(f.stabilized_tip_position.distance_to(palmCenter) - f.length) #distance from finger tip to palm
        nonAbsTipToPalm = f.stabilized_tip_position.distance_to(palmCenter) - f.length
        tipToKnucks = (f.stabilized_tip_position.distance_to(f.bone(0).next_joint))- f.length #distance from finger tip to knuckles
        tipToPalmA = getDistance(f.bone(3).next_joint, hand.palm_position) #distance from finger tip to palm
        
        ##DECIDE FINGER STATUS
        #special logic for thumb
        if (a == 'T'):
            intToPalm = getDistance(f.bone(2).center, hand.palm_position) #distance from finger center to palm
            proxToPalm = getDistance(f.bone(1).prev_joint, hand.palm_position) #distance from beginning of finger to palm
        
            thumbHandAngle = (180*((f.direction.angle_to(hand.direction)))/np.pi)
            if (printRequested):
                print "thumbHandAngle : %f" % thumbHandAngle
            if (angleToHand[a] < thumbUpMargin):
                
                status = 'up' #the thumb is up
                
            else:
                status = 'bent'
                if ((tipToPalm -shortLength) < extendedMargin or abs(angleToPalm[a]- 90) < extendedMargin):
                        status = 'out'
                if ((tipToPalm < thumbInMargin) and angleToHand[a] > 20): #if middle of thumb is closer to palm than base of thumb
                        status = 'in'

        #for all fingers except the thumb
        else:
            if (angleToPalm[a] > angleToHand[a] and (tipToPalmA - fullLength) > extendedMargin):
                
                
                status = 'up' #the finger must be extended

            else:
                #print "tip to palm - short length %f" % (tipToPalm - shortLength)
                status = 'bent'
                
              
                if ((tipToPalmA - intToPalm) > curledMargin and nonAbsTipToPalm > curledMargin):
                    
                    status = 'curled'
                if ((tipToPalmA - shortLength) < downMargin):

                    status = 'down'
                


                elif (angleToHand[a] > 50 and angleToHand[a] < 100):
                    #if the finger to palm angle is small and the finger to hand direction is large, then the finger is probably pointing straight out.
                    status = 'out'
                

        result.append((a, status))
    if (printRequested):
        for a, status in result:
            print ("%s is %s" % (a, status))
    return result

def isTouching(myCoords, bone1, bone2, printRequested):
    """
    returns whether the two coordinates are touching
    that is, the distance is within the isTouchingMargin

    Parameters
    ----------
    myCoords : list of coordinates generated by getCoordList()
    bone1 : name of one bone, i.e. T_Distal
    bone2 :  name of other bone
    printRequested: bool
        if true, prints debug messages

    Returns
    -------
        True if points are in touching distance,
        False if not.
    """
    coords = dict(myCoords)
    thisDistance = coords[bone1].distance_to(coords[bone2]);
    if (printRequested):
            print "this Distance: %f" % thisDistance
    if (thisDistance < isTouchingMargin):
        if (printRequested):
            print "touching"
        return True

    if(printRequested):
        print "not touching"
    return False

def proximalAngles (fingers, hand, printRequested):
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    angle_names = ['T', 'I', 'M', 'R', 'P']
    status = 'unknown'
    first = True;
    result = []
    if (printRequested):
        print "ANGLES FROM EACH FINGER PROXIMAL TO HAND:"

    for a, f in fingers:
        vectorA = f.bone(1).direction
        vectorB = hand.direction
        myAngle = 180*(vectorA.angle_to(vectorB))/np.pi
        if (printRequested):
            print "angle %s is %f" % (angle_names[f.type], myAngle)
        result.append((angle_names[f.type], myAngle))
    return result;

def anglesToHand(fingers, hand, printRequested):
    #compares angles of fingers to normal direction of hand (that is, a vector pointing straight up from wrist to fingers)
    #Returns array with angles in this order:
    #thumb and hand, index and hand, middle and hand, ring and hand, pinky and hand
    #thumbProximal and hand, indexProximal and Hand... etc
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    angle_names = ['T', 'I', 'M', 'R', 'P']
    status = 'unknown'
    first = True;
    result = []
    if (printRequested):
        print "ANGLES FROM EACH FINGER TO HAND:"

    for a, f in fingers:
        vectorA = f.direction
        vectorB = hand.direction
        myAngle = 180*(vectorA.angle_to(vectorB))/np.pi
        if (printRequested):
            print "angle %s is %f" % (angle_names[f.type], myAngle)
        result.append((angle_names[f.type], myAngle))
    return result;


def anglesToPalm(fingers, hand, printRequested):
    #compares angles of fingers to normal direction of palm (that is, a vector pointing straight out of the palm)
    #Returns array with angles in this order:
    #thumb and palm, index and palm, middle and palm, ring and palm, pinky and palm
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    angle_names = ['T', 'I', 'M', 'R', 'P']
    status = 'unknown'
    first = True;
    result = []
    if (printRequested):
        print "ANGLES FROM EACH FINGER TO PALM:"

    for a, f in fingers:
        vectorA = f.direction
        vectorB = hand.palm_normal
        myAngle = 180*(vectorA.angle_to(vectorB))/np.pi
        if (printRequested):
            print "angle %s is %f" % (angle_names[f.type], myAngle)
        result.append((angle_names[f.type], myAngle))
    if (printRequested):
       print "ANGLE FROM TO DOWN AXIS: %f" % (180*(hand.palm_normal.angle_to(Leap.Vector.down))/np.pi)
       print "ROLL: %f" % (180*(hand.direction.roll)/np.pi)
    return result;
    
def getFingerAngles(fingers,hand, printRequested):
    """
    gets angles between each adjacent finger
    returns an array of tuples with name of angle and its value in degrees
    Returns array with angles in this order:
     thumb and index, index and middle, middle and ring, ring and pinky

    Parameters
    ----------
    fingers : FingerList
    hand : hand object
    printRequested: bool
        if true, prints debug messages

    Returns
    -------
    array of tuples 
     each tuple (a,d) consists of the name of angle a (['TI', 'IM', 'MR', 'RP']) and its value in degrees d

    """
    
    finger_names = ['T', 'I', 'M', 'R', 'P']
    angle_names = ['TI', 'IM', 'MR', 'RP']
    status = 'unknown'
    first = True;
    result = []

    for a, f in fingers:
        if (first):
            lastFinger = f;
            lastFingerName = finger_names[f.type];
            first = False
        else: #find the angle between the last finger and the current finger
            vectorA = lastFinger.direction
            vectorB = f.direction
            myAngle = 180*(vectorA.angle_to(vectorB))/np.pi
            if (printRequested):
                print "angle %s is %f" % (angle_names[f.type-1], myAngle)
            lastFinger = f;
            lastFingerName = finger_names[f.type]
            result.append((angle_names[f.type-1], myAngle))

    anglesToPalm(fingers, hand, printRequested)
    anglesToHand(fingers, hand, printRequested)

    return result;
        


def getDistance(vector1, vector2):
    x1 = vector1.x
    y1 = vector1.y
    z1 = vector1.z
    x2 = vector2.x
    y2 = vector2.y
    z2 = vector2.z
    result = math.sqrt( ((x1 - x2)**2)+((y1 - y2)**2) + ((z1 - z2)**2) )
    #print "POINT 1: %d %d %d POINT 2:  %d %d %d DISTANCE: %d" % (x1, y1, z1, x2, y2, z2, result)
    return result

class _Getch: #So, for windows and Unix, this has to be imported differently
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows() #this checks if it's a windows machine
        except ImportError:             #then checks if its unix
            self.impl = _GetchUnix()
    def __call__(self): return self.impl() 

class echo:
    def __init__(self):
        try:
            self = _echoWindows();
        except ImportError:
            self = os.system("stty echo")
    def __call__(self): return self

#IF
class _GetchUnix: #this is for Unix Computers
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

#IF
class _echoWindows:#this is for windows
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getwche()


class _GetchWindows:#this is for windows
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

    
getch = _Getch()

button_delay = 0.2


def printFrameInfo(frame):
    frame = frame
    
    if not (frame.hands.is_empty):

        for hand in frame.hands:
            
            handType = "left_Hand" if hand.is_left else "rightHand"
            
            print "%f %f %f" % (
                                                hand.palm_position.x, hand.palm_position.y, hand.palm_position.z )
                
                
                
            
            # Get fingers
            for finger in hand.fingers:
                
            
                # Get bones
                for b in range(0, 4):
                    bone = finger.bone(b)
                    print "%f %f %f" % (
                                            
                                              bone.next_joint.x, bone.next_joint.y, bone.next_joint.z )







def getFingers(frame):
    finger_names = ['T', 'I', 'M', 'R', 'P']
    frame = frame
    result = []
    if not (frame.hands.is_empty):
        for hand in frame.hands:
            
            
            # Get fingers
            for finger in hand.fingers:
                #fingerLength = 0.0
                fingerName = finger_names[finger.type]
                
                
                result.append((fingerName, finger))

    return result

def getFingerLengths(frame):
    finger_names = ['T', 'I', 'M', 'R', 'P']
    frame = frame
    result = []
    fingerLength = 0.0
    if not (frame.hands.is_empty):
        for hand in frame.hands:
            
            
            
            # Get fingers
            for finger in hand.fingers:
                #fingerLength = 0.0
                fingerName = finger_names[finger.type]
                
                
                result.append((fingerName, finger.length))
    
            
        return result

def getCoordList(frame):
    finger_names = ['T', 'I', 'M', 'R', 'P']
    bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal']
    frame = frame
    result = []
    if not (frame.hands.is_empty):
        for hand in frame.hands:
            
            handType = "left_Hand" if hand.is_left else "rightHand"
            
            result.append((handType, hand.palm_position))
            
            
            
            # Get fingers
            for finger in hand.fingers:
                
                fingerName = finger_names[finger.type]
                
                # Get bones
                for b in range(0, 4):
                    bone = finger.bone(b)
                    result.append(
                                  (fingerName+"_"+ bone_names[bone.type],
                                   bone.next_joint))
        
            return result


# def printFrameInfo(Frame):


class SampleListener(Leap.Listener):
    finger_names = ['T', 'I', 'M', 'R', 'P']
    bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal  ']
    state_names = ['STATE_INVALID', 'STATE_START', 'STATE_UPDATE', 'STATE_END']
    first = False
    firstFrameId = 0
    mostRecentFrame = 0
    initialTime = 0 #timestamp of first frame in ms

    frames = []
        

    def on_init(self, controller):
        print "Initialized"
        self.first = True
        self.firstFrameId = 0
        self.mostRecentFrameId = 0
    
    
    
    def on_connect(self, controller):
        print "Connected"
        
        # Enable gestures
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);
    
    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        print "Disconnected"
    
    def on_exit(self, controller):
        print "EXIT"
    
    def on_frame(self, controller):
        
        # Get the most recent frame and report some basic information
        frame = controller.frame()
        self.frames.append(frame)
        if (self.first):
            print("RECORDING... Hit space to get sign, 2 to print data, 3 to print finger length/coordinates, f to print data to file, and p to pause.")
            initialTime = frame.timestamp
            self.first = False
        else:
            self.mostRecentFrame = frame
            if (len(self.frames) > maxFrames):
                del self.frames[0] #delete the oldest
            #print("Most recent frame: " + str(self.mostRecentFrameId))
            #self.printFrameInfo(self.mostRecentFrameId)


    def state_string(self, state):
        if state == Leap.Gesture.STATE_START:
            return "STATE_START"
            
        if state == Leap.Gesture.STATE_UPDATE:
            return "STATE_UPDATE"
        
        if state == Leap.Gesture.STATE_STOP:
            return "STATE_STOP"
            
        if state == Leap.Gesture.STATE_INVALID:
            return "STATE_INVALID"
    
def framesEqual(frame1, frame2): 
    """framesEqual() function returns true if the 2 frames are about equal

        takes 2 frames and checks each finger (each frame should only have 1 hand)

        Parameters
        ----------
        frame1: frame
            first frame
        frame2: frame
            second frame to compare

        Returns
        -------
        bool
            true if frames are about equal, false if not
        """
    if (frame1.fingers.is_empty or frame2.fingers.is_empty):
        return False

    for finger_type in range(0,5): #iterates from 0(TYPE_THUMB) to 4 (TYPE_PINKY):
        group1 = getFingers(frame1)
        group2 = dict(getFingers(frame2)) 

        if(len(group1) != len(group2)): #if one frame has more fingers than the other frame
            #print f.stabilized_tip_position
            return False

        for a,f in group1:
            distance = (f.stabilized_tip_position).distance_to(group2[a].stabilized_tip_position)
            if (distance >= maxDistance):
                return False


    return True


def isSteady(frameList, frameCount): 
    """ isSteady function returns true if the hand is steady

            checks if the last (framecount) frames in the list (frameList) are about equal
            if so, the hand is steady, return true. otherwise return false.

            Parameters
            ----------
            frameList : list of frames
                list of recent frames, should have more than framecount
            frameCount : int
                number of frames to check

            Returns
            -------
            bool
                true if hand is steady, false otherwise.
    """
    total = len(frameList)

    frame1 = frameList[total - frameCount] #first frame that we want to check
    i = (total - frameCount + 1)           #index of the frame after that one
    frame2 = frameList[i]

    for x in range(i, frameCount):          #iterate through the selected frames

        if (not(framesEqual(frame1, frame2))): #if they're not about equal,
            print "NOT STEADY"
            return False                    #then quit
        frame1 = frame2                     #otherwise, iterate to the next 2 frames.
        frame2 = frameList[x]
    #print "STEADY"
    return True                             #return true if you get through the entire loop 



def isSteady(listener):
    if (framesEqual(listener.frames[-1], listener.frames[-2]) and framesEqual(listener.frames[-2], listener.frames[-3])):
        return True
    return False



def getFPS(frames, var, printRequested):
    #initialize some things
    timestamp_a = frames[0].timestamp
    frameLoop = 1
    avgTimeDifference = 0

    #loop through frames specified and print out the time difference between each pair
    while (frameLoop <= int(var)-1): 
        timestamp_b = frames[frameLoop].timestamp
        timeDifference = (timestamp_b - timestamp_a)
        if(printRequested):
            print "frame %d to %d: %d microseconds" % (frameLoop, frameLoop+1, timeDifference)
        timestamp_a = timestamp_b
        frameLoop += 1
        avgTimeDifference += timeDifference
    avgTimeDifference /= (int(var)-1)
    if(printRequested):
        print "average time difference between frames in microseconds :", avgTimeDifference
    # the average frames per second is 1000000 microseconds(the number of micros in a single second)
    # divided by the average time it takes to get a new frame
    avgFPS = 1000000 / avgTimeDifference 
    if(printRequested):
        print "average frames per second: ", avgFPS
    return avgFPS
#######################################################

def main():
    """Main Function, body of program"""
    paused = False
    recording = False

    # Create a sample listener and controller
    listener = SampleListener()
    controller = Leap.Controller()

    frames = listener.frames        # list, store recent frames


    currentFPS = 0

    myCoords = []
    fingerStatuses = []
    myFingerList = []
    i = 0
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%H-%M-%S')
    
    
    
    # ========================================================#
    #    Keep this process running until Enter is pressed     #
    #
    print "Press r to begin."
    #frame2 = controller.frame()
    try:
        ch = getch()
        while(not(ch == "q")):


            #---------------
            # q     -> quits program
            # r     -> resume recording 
            # p     -> pause recording
            # t     -> print timestamps

            

            if ((ch == "r" or ch == "R") and not recording):   #RESUME RECORDING
                print("Hit any key to resume recording. Hit p to pause")
                recording = True

            if (ch == "p"):                     #PAUSE RECORDING
                print("Hit r to resume.")
                paused = True
                controller.remove_listener(listener)
                recording = False

            mostRecentFrame = listener.mostRecentFrame
            frameCount = len(frames)

            if (ch == "t"):
                print "enter # of frames"
                var = raw_input("enter # of frames 1 - %d or hit enter for all\n" % frameCount)
                if (not var.isdigit()):
                    var = frameCount

                currentFPS = getFPS(frames, int(var), True)

            #---------------
            # OTHER OPTIONS:
            # 1         -> prints FPS
            # 2         -> prints finger lengths, statuses, and distances from palm
            # 3         -> prints finger coordinates and length
            # 4         -> prints finger angles between each other and palm
            # spacebar  -> manually sends frame, checks for a sign

            if (ch == "1"):
                currentFPS =  getFPS(frames, frameCount, False)
                print "CURRENT FPS: ", currentFPS
            if (ch == "2" and recording): #PRINT FINGER STATUSES
                
                myFingerList = getFingers(mostRecentFrame)
                getFingerStatuses(myFingerList, mostRecentFrame.hands.frontmost, True);
            if (ch == "3" and recording): #PRINT FINGER DISTANCES AND LENGTH 
                myCoords = getCoordList(mostRecentFrame)
                palmCenter = mostRecentFrame.hands.frontmost.palm_position
                myFingerList = getFingers(mostRecentFrame)
                if myFingerList:
                    for a, y in myFingerList:
                        print "%s full length: %f" % (a, y.length + y.bone(0).length)
                        print "%s length: %f" % (a, y.length)
                        print "%s  %f tip distance to palm" % (a, (y.stabilized_tip_position.distance_to(palmCenter) - y.length))
                        print "%s  %f tip distance to knucks" % (a, (y.stabilized_tip_position.distance_to(y.bone(0).next_joint))- y.length)
                        print "%s  %f knucks distance to palm" % (a, (y.bone(0).next_joint.distance_to(palmCenter)))
                        print "%s  %f middle joint distance to palm" % (a, abs(y.bone(1).center.distance_to(palmCenter)))

            if (ch == "4" and recording): #PRINT FINGER ANGLES
                print "FINDING ANGLES..."
                myFingerList = getFingers(mostRecentFrame)
                getFingerAngles(myFingerList, mostRecentFrame.hands.frontmost, True);
            
            if (ch == "5" and recording): #test function
                myFingerList = getFingers(mostRecentFrame)
                palmCenter = mostRecentFrame.hands.frontmost.palm_position
                if myFingerList:
                    for a, y in myFingerList:
                        print "%s length: %f" % (a, y.length)
                        print "%s  %f tip distance to palm" % (a, (y.stabilized_tip_position.distance_to(palmCenter) - y.length))
                        print "%s  %f tip distance to knucks" % (a, (y.stabilized_tip_position.distance_to(y.bone(0).next_joint))- y.length)
                        print "%s  %f knucks distance to palm" % (a, (y.bone(0).next_joint.distance_to(palmCenter)))
                        print "%s  %f middle joint distance to palm" % (a, abs(y.bone(1).center.distance_to(palmCenter)))



            if (ch == "m" and recording): #print hand motion information
                myFingerList = getFingers(mostRecentFrame)
                myHand = mostRecentFrame.hands.frontmost
                start_frame = frames[frameCount-int(getFPS(frames, frameCount, False) *0.5)] #start from the beginning of the last half second
                print ("--------------\nTranslation Vector:")
                print (myHand.translation(start_frame))

                if (myHand.translation(start_frame).y > 50):
                    print "\n==================\n     UP!!   \n=================="

                print ("Probability: %f") % myHand.translation_probability(start_frame)
                print ("Rotation Matrix:")
                print (myHand.rotation_matrix(start_frame))
                print ("Probability: %f") % myHand.rotation_probability(start_frame)
                print ("Rotational Angle:")
                print (myHand.rotation_angle(start_frame))


                if (myHand.rotation_angle(start_frame) > 2):
                    print "==================\n      FLIPPED!    \n==================="

                print ("Around Rotational Axis:")
                print (myHand.rotation_axis(start_frame))
              
            #~ GET SIGN ~#
            if (ch == " " and  recording): #PRINT CURRENT SIGN
                if (isSteady(listener)):
                    myCoords = getCoordList(mostRecentFrame)
                    myFingerList = getFingers(mostRecentFrame)
                    myHand = mostRecentFrame.hands.frontmost
                    fingerStatuses = getFingerStatuses(myFingerList, myHand, False)

                    getSign(fingerStatuses, mostRecentFrame.hands.frontmost, anglesToPalm(myFingerList, myHand, False), getFingerAngles(myFingerList,myHand, False), isTouching(myCoords, 'T_Distal', 'M_Distal', False))
                else:
                    print "Hand is unsteady."
            if (ch == "\n" and  recording):
                if (isSteady(listener)):
                    print "STEADY"
                else:
                    print "NOT STEADY"

            if(recording):
                controller.add_listener(listener)


                


            ch = getch()

        recording = False

    #                                                         #
    # ========================================================#

    except KeyboardInterrupt:     
        key = echo()
    # os.system("stty echo")
        pass
    finally:
        key = echo()
       # os.system("stty echo")
        controller.remove_listener(listener) #Remove the sample listener when done



if __name__ == "__main__":
  main()

