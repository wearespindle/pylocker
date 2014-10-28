#!/usr/bin/env python

import cv
import schedule
import sys
import time
import subprocess
import argparse
import platform


class PyLocker:

    def __init__(self, args):
        self.locktime = args.locktime
        self.locker = args.locker
        self.treshold = args.treshold
        self.system = platform.system()

        self.last_movement = time.time()
        self.capture = cv.CaptureFromCAM(-1)
        cv.NamedWindow("PyLocker", 1)
        schedule.every(0.1).seconds.do(self.check_lock)


    def check_lock(self):
        diff_time = time.time() - self.last_movement
        sys.stdout.write('Idle for: %.2f seconds \r' % diff_time)
        sys.stdout.flush()
        if diff_time > self.locktime:
            if (self.system == 'Darwin'):
                subprocess.call('/System/Library/CoreServices/Menu\ Extras/user.menu/Contents/Resources/CGSession -suspend', shell=True)
            else:
                subprocess.call(self.locker, shell=True)


    def run(self):
        self.frame_count = 0
        sms_count = 0
        # Capture first frame to get size
        frame = cv.QueryFrame(self.capture)
        color_image = cv.CreateImage(cv.GetSize(frame), 8, 3)
        grey_image = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U, 1)
        moving_average = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_32F, 3)

        first = True

        while True:
            schedule.run_pending()
            color_image = cv.QueryFrame(self.capture)
            # Smooth to get rid of false positives
            cv.Smooth(color_image, color_image, cv.CV_GAUSSIAN, 3, 0)
            if first:
                difference = cv.CloneImage(color_image)
                temp = cv.CloneImage(color_image)
                cv.ConvertScale(color_image, moving_average, 1.0, 0.0)
                first = False
            else:
                cv.RunningAvg(color_image, moving_average, 0.020, None)

            # Convert the scale of the moving average.
            cv.ConvertScale(moving_average, temp, 1.0, 0.0)
            # Minus the current frame from the moving average.
            cv.AbsDiff(color_image, temp, difference)
            # Convert the image to grayscale.
            cv.CvtColor(difference, grey_image, cv.CV_RGB2GRAY)
            # Convert the image to black and white.
            cv.Threshold(grey_image, grey_image, 70, 255, cv.CV_THRESH_BINARY)
            # Dilate and erode to get people blobs
            cv.Dilate(grey_image, grey_image, None, 18)
            cv.Erode(grey_image, grey_image, None, 10)

            storage = cv.CreateMemStorage(0)
            contour = cv.FindContours(grey_image, storage, cv.CV_RETR_CCOMP, cv.CV_CHAIN_APPROX_SIMPLE)
            points = []

            while contour:
                self.frame_count += 1
                sms_count += 1
                bound_rect = cv.BoundingRect(list(contour))
                contour = contour.h_next()
                pt1 = (bound_rect[0], bound_rect[1])
                pt2 = (bound_rect[0] + bound_rect[2], bound_rect[1] + bound_rect[3])
                points.append(pt1)
                points.append(pt2)
                cv.Rectangle(color_image, pt1, pt2, cv.CV_RGB(255, 0, 0), 1)

            if len(points):
                center_point = reduce(lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), points)
                cv.Circle(color_image, center_point, 40, cv.CV_RGB(255, 255, 255), 1)
                cv.Circle(color_image, center_point, 30, cv.CV_RGB(255, 100, 0), 1)
                cv.Circle(color_image, center_point, 20, cv.CV_RGB(255, 255, 255), 1)
                cv.Circle(color_image, center_point, 10, cv.CV_RGB(255, 100, 0), 1)

            cv.ShowImage("PyLocker", color_image)
            #send frame each x frames
            if self.frame_count >= self.treshold:
                self.frame_count = 0
                self.last_movement = time.time()

            # Listen for ESC key
            c = cv.WaitKey(7) % 0x100
            if c == 27:
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--locktime', type=int, default=10, help='lock time')
    parser.add_argument('--treshold', type=int, default=1, help='movement treshold')
    parser.add_argument('--locker', type=str, default='i3lock', help='screenlocker executable')

    args = parser.parse_args()
    t = PyLocker(args)
    t.run()
