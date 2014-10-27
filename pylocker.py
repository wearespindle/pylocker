#!/usr/bin/env python

import cv
import schedule
import time
import subprocess


class TaardLock:

    def __init__(self):
        self.last_movement = time.time()
        self.state = 'running'
        self.capture = cv.CaptureFromCAM(-1)
        cv.NamedWindow("Target", 1)
        schedule.every(1).seconds.do(self.check_lock)

    def check_lock(self):
        diff_time = time.time() - self.last_movement
        print 'Idle for: %s seconds' % diff_time
        if diff_time > 10:
            if self.state != 'locked':
                print "LOCK IT!"
                subprocess.call(['i3lock'])
            self.state = 'locked'

    def run(self):
        frame_count = 0
        frame_limiter = 10
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
                frame_count += 1
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

            cv.ShowImage("Target", color_image)
            #send frame each x frames
            if frame_count >= frame_limiter:
                frame_limiter += 10
                self.last_movement = time.time()
                print "Still alive..."

            # Listen for ESC key
            c = cv.WaitKey(7) % 0x100
            if c == 27:
                break

if __name__ == "__main__":
    t = TaardLock()
    t.run()
