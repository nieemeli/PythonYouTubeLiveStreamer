from tkinter import *
from tkinter import messagebox
import PIL
from PIL import ImageTk, Image
import cv2
import subprocess
from sys import exit
import numpy
import threading


class App:

    def __init__(self):

        root = Tk()
        root.title("MiniOBS")
        root1 = Frame(root, height=400, width=700, background="#242020")
        root1.pack(side=BOTTOM)


        class tkCamera(Frame):

            def __init__(self, window, video_source=0):
                self.window = window
                print('window:', self.window)
                self.video_source = video_source
                self.vid = MyVideoCapture(self.video_source)
                self.canvas = Canvas(window, width=self.vid.width,
                                    height=self.vid.height)
                self.canvas.pack()

                self.delay = 15  # After it is called once, the update method will be automatically called every delay milliseconds
                self.update_widget()

            def update_widget(self):

                ret, frame = self.vid.get_frame()  # Get a frame from the video source

                if ret:
                    self.image = PIL.Image.fromarray(frame)
                    self.photo = PIL.ImageTk.PhotoImage(image=self.image)
                    self.canvas.create_image(0, 0, image=self.photo, anchor=NW)
                else:
                    messagebox.showinfo("Information", "Cant find video stream!")
                    return 0

                self.window.after(self.delay, self.update_widget)


        class MyVideoCapture:

            def __init__(self, video_source=0):
                self.vid = cv2.VideoCapture(video_source)  # Open the video source
                if not self.vid.isOpened():
                    raise ValueError("Unable to open video source", video_source)
                self.width = 300
                self.height = 250

            def get_frame(self):
                if self.vid.isOpened():
                    ret, frame = self.vid.read()
                    if ret:
                        frame = cv2.resize(frame, (300, 250))
                        # Return a boolean success flag and the current frame converted to BGR
                        return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    else:
                        return (ret, None)
                else:
                    return ('video not opened!')

            def __del__(self):
                if self.vid.isOpened():
                    self.vid.release()  # Release the video source when the object is destroyed


        videocanvas_left = Frame(root1, height=400, width=600, background="#242020")
        videocanvas_left.pack(side=LEFT)
        videocanvas_right = Frame(root1, height=400, width=600, background="#242020")
        videocanvas_right.pack(side=RIGHT)

        video_streams_list = []  # global array for saving video stream addresses


        def validate_and_add_stream(input):
            if (input == '0'):
                input = 0
            if (len(video_streams_list) == 0):
                video_streams_list.append(input)
                try:
                    vid = tkCamera(videocanvas_left, input)
                except ValueError:
                    messagebox.showinfo("Information", "Stream source invalid!")
                    video_streams_list.pop()
            elif (len(video_streams_list) == 1):
                video_streams_list.append(input)
                print('len of list', len(video_streams_list))
                try:
                    vid = tkCamera(videocanvas_right, input)
                except ValueError:
                    messagebox.showinfo("Information", "Stream source invalid!")
                    video_streams_list.pop()
            elif (len(video_streams_list) == 2):
                messagebox.showinfo("Information", "2 streams already added!")


        def catch_video_to_ui():
            input = ent_video_source.get()
            validate_and_add_stream(input)


        def start_broadcasting():

            def streaming_loop():
                youtube_stream_url = "rtmp://a.rtmp.youtube.com/live2/"
                streamkey = ent_broadcasting.get()
                url = str(youtube_stream_url) + str(streamkey)

                ffmpeg_command = ['ffmpeg',
                                '-f', 'rawvideo',
                                '-pix_fmt', 'bgr24',
                                '-s', '600x400',
                                '-i', '-',
                                '-ar', '44100',
                                '-ac', '2',
                                '-acodec', 'pcm_s16le',
                                '-f', 's16le',
                                '-ac', '2',
                                '-i', '/dev/zero',
                                '-acodec', 'aac',
                                '-ab', '128k',
                                '-strict', 'experimental',
                                '-vcodec', 'h264',
                                '-pix_fmt', 'yuv420p',
                                '-g', '50',
                                '-vb', '1000k',
                                '-profile:v', 'baseline',
                                '-preset', 'ultrafast',
                                '-r', '30',
                                '-f', 'flv',
                                url]

                pipe = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

                cap1 = cv2.VideoCapture(video_streams_list[0])
                cap2 = cv2.VideoCapture(video_streams_list[1])

                while True:
                    ret1, frame1 = cap1.read()
                    ret2, frame2 = cap2.read()

                    h, w, c = frame1.shape
                    h1, w1, c1 = frame2.shape

                    if h != h1 or w != w1:  # resize right img to left size
                        frame2 = cv2.resize(frame2, (w, h))
                    image_of_both = numpy.hstack((frame1, frame2))
                    up_width = 600
                    up_height = 400
                    up_points = (up_width, up_height)
                    # let's upscale the image using new  width and height
                    final_image = cv2.resize(
                        image_of_both, up_points, interpolation=cv2.INTER_LINEAR)
                    print('Resized Dimensions : ', final_image.shape)
                    if (cv2.waitKey(1) & 0xFF == ord('q')):
                        break
                    pipe.stdin.write(final_image.tostring())

            streaming_thread = threading.Thread(target=streaming_loop)
            streaming_thread.start()


        def stop_broadcasting():
            print("Pressed stop broadcasting button")


        lbl_source = Label(text="Add video URL")
        lbl_source.pack()

        ent_video_source = Entry(width=50)
        ent_video_source.pack()

        btn_video_source = Button(text="Catch video to UI", command=catch_video_to_ui
                                )
        btn_video_source.pack()

        lbl_destination = Label(root, text="Add your YouTube-streamkey")
        lbl_destination.pack()

        ent_broadcasting = Entry(width=50)
        ent_broadcasting.pack()

        btn_broadcasting = Button(
            text="Start livestreaming to YouTube", command=start_broadcasting
        )
        btn_broadcasting.pack()

        root.mainloop()


if __name__ == "__main__":
    App()

