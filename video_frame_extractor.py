import os
import uuid
import requests
import cv2
from PIL import Image
import imagehash
import shutil
from typing import Dict, Any, List

class VideoFrameExtractor:
    def __init__(self, driver) -> None:
        """
        Initialize the VideoFrameExtractor with a Driver instance.

        :param driver: An instance of the Driver class.
        """
        self.driver = driver
        self.handle_videos()

    def download_video(self, video: Dict[str, Any]) -> str:
        """
        Downloads a video from a given URL and saves it locally.

        :param video: A dictionary containing video details, including the video URL.
        :return: The local path to the downloaded video.
        :raises: requests.exceptions.RequestException if the download fails.
        """
        download_folder = "download/videos"
        os.makedirs(download_folder, exist_ok=True)

        video_url = video["video"]
        video_extension = os.path.splitext(video_url)[-1]
        unique_filename = f"{uuid.uuid4()}{video_extension}"
        download_path = os.path.join(download_folder, unique_filename)
        self.driver.record_log('info', f"Starting the download from: {video_url}")
        
        try:
            response = requests.get(video_url)
            response.raise_for_status()
            with open(download_path, 'wb') as file:
                file.write(response.content)
            self.driver.record_log('info', f"Video saved successfully to {download_path}")
            return download_path
        except requests.exceptions.RequestException as e:
            self.driver.record_log('error', f"Failed to download video from {video_url}: {e}")
            raise

    def remove_similar_frames(self, frames_dir: str) -> None:
        """
        Removes similar frames from a directory by comparing their hashes.

        :param frames_dir: The directory containing the video frames.
        """
        image_hashes = {}
        path = os.path.abspath(frames_dir)
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            if os.path.isfile(file_path):
                with Image.open(file_path) as img:
                    img_hash = imagehash.average_hash(img)
                for existing_hash, existing_filename in image_hashes.items():
                    similarity_distance = img_hash - existing_hash
                    if similarity_distance <= 5:
                        os.remove(file_path)
                        break
                else:
                    image_hashes[img_hash] = filename
    
    def upload_frames(self, frames_dir: str, photos_group_id: str) -> None:
        """
        Uploads frames to a remote server and deletes the local frames directory after uploading.

        :param frames_dir: The directory containing the video frames.
        :param photos_group_id: The ID of the photo group to which frames should be uploaded.
        """
        path = os.path.abspath(frames_dir)
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            if os.path.isfile(file_path):
                self.driver.record_log('info', f'Starting upload of {filename}')
                with open(file_path, 'rb') as photo:
                    photos = {'photo': (filename, photo)}
                    try:
                        self.driver.send_http_request('POST', f"photos/{photos_group_id}/add", photos, files=True)
                        self.driver.record_log('info', f'Successfully uploaded {filename}')
                    except:
                        self.driver.record_log('error', f'Failed to upload {filename}.')

        shutil.rmtree(frames_dir)
    
    def mark_video_as_done(self, video):
        """
        Marks a video as published on the server.

        :param video: A dictionary containing video details, including the video ID.
        """
        self.driver.record_log('info', f'Marking the video {video["id"]} as done')
        data = {"state": "published"}
        try:
            self.driver.record_log('info', f'Video {video["id"]} marked as done')
            self.driver.send_http_request('POST', f"videos/{video['id']}/published", data)
        except:
            self.driver.record_log('error', f"Failed to mark {video['id']} as done.")
        
    def extract_frames(self, video_path: str) -> str:
        """
        Extracts frames from a video and saves them to a directory.

        :param video_path: The path to the video file.
        :return: The directory containing the extracted frames.
        """
        video_file = cv2.VideoCapture(video_path)
        if not video_file.isOpened():
            self.driver.record_log('error', "Can't read video.")
            return False
        
        frames_dir = os.path.splitext(video_path)[0]
        os.makedirs(frames_dir)
        frame_count = 0
        success = True

        while success:
            success, frame = video_file.read()
            if success:
                frame_path = os.path.abspath(frames_dir+"\\"+str("{:0>4d}".format(frame_count))+".jpg")
                cv2.imwrite(frame_path, frame)
                frame_count += 1
            
        video_file.release()
        os.remove(os.path.abspath(video_path))
        return frames_dir

    def handle_videos(self) -> None:
        """
        Handles the entire process of downloading, processing, and uploading videos.
        """
        videos = self.driver.send_http_request('GET', 'videos/get')

        if videos:
            self.driver.record_log('info', "Fetched new videos successfully.")
            for video in videos:
                try:
                    video_path = self.download_video(video)
                    frames_dir = self.extract_frames(video_path)
                    self.remove_similar_frames(frames_dir)
                    self.upload_frames(frames_dir, video['photos_group_id'])
                    self.mark_video_as_done(video)
                except Exception as e:
                    self.driver.record_log('error', f"Failed to process video {video.get('id', 'unknown')}: {e}")
        else:
            self.driver.record_log('info', "No new videos.")