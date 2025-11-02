import cv2
import numpy as np
import os
from typing import Optional, Tuple, List
from pathlib import Path

# Stream URL for the camera
STREAM_URL = "https://interactions.ics.unisg.ch/61-102/cam4/live-stream"

# Default calibration file paths
INTRINSICS_PATH = "calibration_data/intrinsics.npz"
HOMOGRAPHY_PATH = "calibration_data/homography.npz"

# Intrinsic and coordinate transformation calibration class
class CameraCalibrator:
    
    def __init__(self, intrinsics_path: str = INTRINSICS_PATH, 
                 homography_path: str = HOMOGRAPHY_PATH):
        self.intrinsics_path = intrinsics_path
        self.homography_path = homography_path
        
        # Intrinsic parameters
        self.camera_matrix = None  # 3x3 camera matrix (focal length, principal point)
        self.dist_coeffs = None    # Distortion coefficients
        
        # Coordinate transformation
        self.homography_matrix = None  # 3x3 homography matrix for pixel->robot mapping
        
        # Ensure calibration directory exists
        Path(self.intrinsics_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.homography_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Calibrate camera intrinsic parameters using a checkerboard pattern
    def calibrate_intrinsics(self, stream_url: str, 
                            checkerboard_size: Tuple[int, int] = (9, 6),
                            square_size_mm: float = 20.0,
                            num_images: int = 20) -> bool:
        print("\n===Intrinsic Camera Calibration ===")
        print(f"Checkerboard size: {checkerboard_size[0]}x{checkerboard_size[1]} inner corners")
        print(f"Square size: {square_size_mm} mm")
        print(f"Capturing {num_images} calibration images..." + "\n")
        print("Instructions:")
        print("  - Hold checkerboard in front of camera")
        print("  - Press SPACE to capture when checkerboard is detected")
        print("  - Move checkerboard to different positions/angles")
        print("  - Press 'q' when done (after capturing enough images)")
        
        # Prepare object points (3D points in real world)
        objp = np.zeros((checkerboard_size[0] * checkerboard_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:checkerboard_size[0], 
                               0:checkerboard_size[1]].T.reshape(-1, 2)
        objp *= square_size_mm  # Convert to mm
        
        # Arrays to store object points and image points
        objpoints = []  # 3D points in real world
        imgpoints = []  # 2D points in image plane
        
        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            print(f"Error: Could not open camera stream: {stream_url}")
            return False
        
        images_captured = 0
        
        while images_captured < num_images:
            ret, frame = cap.read()
            if not ret:
                print("Warning: Could not read frame from stream")
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Find checkerboard corners
            ret_corners, corners = cv2.findChessboardCorners(
                gray, checkerboard_size, 
                cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE
            )
            
            # Draw corners if found
            frame_display = frame.copy()
            if ret_corners:
                cv2.drawChessboardCorners(frame_display, checkerboard_size, corners, ret_corners)
                text = f"Checkerboard detected! [{images_captured}/{num_images}] Press SPACE to capture"
                cv2.putText(frame_display, text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                text = f"Move checkerboard into view [{images_captured}/{num_images}]"
                cv2.putText(frame_display, text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            # Display the frame with the checkerboard
            cv2.imshow("Intrinsic Calibration", frame_display)
            
            # Wait for user input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # Exit if 'q' is pressed
                break
            elif key == ord(' ') and ret_corners: # [SPACE] to capture the image
                # Refine corner positions
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                
                objpoints.append(objp)
                imgpoints.append(corners_refined)
                images_captured += 1
                print(f"Captured image {images_captured}/{num_images}")
        
        # Release the camera and close the window
        cap.release()
        cv2.destroyAllWindows()
        
        # At least 3 calibration images are required
        if len(objpoints) < 3:
            print(f"Error: Need at least 3 calibration images, got {len(objpoints)}")
            return False
        print(f"\nCalibrating camera with {len(objpoints)} images...")
        
        # Perform calibration
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, gray.shape[::-1], None, None
        )
        
        # False, if calibration failed
        if not ret:
            print("Error: Calibration failed")
            return False
        
        # Save the camera matrix and distortion coefficients
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        
        # Calculate reprojection error
        total_error = 0
        for i in range(len(objpoints)):
            imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], 
                                             camera_matrix, dist_coeffs)
            error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            total_error += error
        mean_error = total_error / len(objpoints)
        
        # Print the calibration results
        print(f"\nCalibration successful!")
        print(f"Camera matrix:\n{camera_matrix}")
        print(f"Distortion coefficients: {dist_coeffs.flatten()}")
        print(f"Mean reprojection error: {mean_error:.3f} pixels")
        
        # Save calibration data
        np.savez(self.intrinsics_path, 
                camera_matrix=camera_matrix, 
                dist_coeffs=dist_coeffs)
        print(f"Saved intrinsic calibration to: {self.intrinsics_path}")
        
        return True
    
    # Calibrate coordinate transformation from pixels to robot world coordinates
    def calibrate_coordinate_transform(self, stream_url: str, 
                                      min_points: int = 4) -> bool:
        print("\n=== Coordinate Transformation Calibration ===")
        print(f"Click on {min_points}+ reference points in the image")
        print("Press ESC when done selecting points")
        
        clicked_points = []
        frame = None  # Initialize frame variable
        
        # Mouse callback for selecting calibration points
        def click_event(event, x, y, flags, param):
            nonlocal clicked_points, frame
            if event == cv2.EVENT_LBUTTONDOWN and frame is not None:
                clicked_points.append((x, y))
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                cv2.putText(frame, f"{len(clicked_points)}", (x + 10, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Coordinate Calibration", frame)
                print(f"Point {len(clicked_points)}: Pixel coordinates = ({x}, {y})")
        
        # Open the camera stream
        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            print(f"Error: Could not open camera stream: {stream_url}")
            return False
        
        # Display the frame with the calibration points
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Warning: Could not read frame from stream")
                break
            display = frame.copy()
            for i, pt in enumerate(clicked_points):
                cv2.circle(display, pt, 5, (0, 255, 0), -1)
                cv2.putText(display, str(i + 1), (pt[0] + 10, pt[1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Coordinate Calibration", display)
            cv2.setMouseCallback("Coordinate Calibration", click_event)
            
            # Wait for user input
            key = cv2.waitKey(10) & 0xFF
            if key == 27:  # ESC
                break
        
        # Release the camera and close the window
        cap.release()
        cv2.destroyAllWindows()
        
        # At least 4 calibration points are required
        if len(clicked_points) < min_points:
            print(f"Error: Need at least {min_points} points, got {len(clicked_points)}")
            return False
        
        # Enter the robot world coordinates for each point
        print(f"\nEnter robot world coordinates (in mm) for each point:")
        print("(X and Y coordinates relative to robot origin)")
        robot_points = []
        for i, (px, py) in enumerate(clicked_points):
            x = float(input(f"\nPoint {i+1} - Robot X coordinate (mm): "))
            y = float(input(f"Point {i+1} - Robot Y coordinate (mm): "))
            robot_points.append((x, y))
        
        # Calculate homography matrix
        src_points = np.array(clicked_points, dtype=np.float32)
        dst_points = np.array(robot_points, dtype=np.float32)
        
        H, mask = cv2.findHomography(src_points, dst_points)
        
        # False, if homography matrix could not be computed
        if H is None:
            print("Error: Could not compute homography matrix")
            return False
        
        self.homography_matrix = H
        
        # Save homography matrix
        np.savez(self.homography_path, homography=H)
        print(f"\nCoordinate transformation calibrated!")
        print(f"Homography matrix:\n{H}")
        print(f"Saved to: {self.homography_path}")
        
        # Test transformation with first point
        test_pixel = src_points[0:1]
        test_robot = cv2.perspectiveTransform(test_pixel.reshape(-1, 1, 2), H)[0][0]
        print(f"\nTest transformation:")
        print(f"  Pixel ({test_pixel[0][0]:.1f}, {test_pixel[0][1]:.1f}) -> "
              f"Robot ({test_robot[0]:.1f}, {test_robot[1]:.1f}) mm")
        print(f"  Expected: ({dst_points[0][0]:.1f}, {dst_points[0][1]:.1f}) mm")
        
        return True
    

    # Load calibration data from files
    def load_calibration(self) -> Tuple[bool, bool]:
        intrinsics_loaded = False
        homography_loaded = False
        
        # Load intrinsic calibration
        if os.path.exists(self.intrinsics_path):
            try:
                data = np.load(self.intrinsics_path)
                self.camera_matrix = data['camera_matrix']
                self.dist_coeffs = data['dist_coeffs']
                intrinsics_loaded = True
                print(f"Loaded intrinsic calibration from: {self.intrinsics_path}")
            except Exception as e:
                print(f"Warning: Could not load intrinsic calibration: {e}")
        
        # Load homography matrix
        if os.path.exists(self.homography_path):
            try:
                data = np.load(self.homography_path)
                self.homography_matrix = data['homography']
                homography_loaded = True
                print(f"Loaded coordinate transformation from: {self.homography_path}")
            except Exception as e:
                print(f"Warning: Could not load homography: {e}")
        
        return intrinsics_loaded, homography_loaded
    

    # Undistort a pixel coordinate using intrinsic calibration
    def undistort_point(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        # Return original if not calibrated
        if self.camera_matrix is None or self.dist_coeffs is None:
            return pixel_x, pixel_y  # Return original if not calibrated
        
        # Undistort the point
        point = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
        undistorted = cv2.undistortPoints(point, self.camera_matrix, 
                                         self.dist_coeffs, P=self.camera_matrix)
        return float(undistorted[0][0][0]), float(undistorted[0][0][1])
    

    # Transform pixel coordinates to robot world coordinates
    def pixel_to_robot(self, pixel_x: float, pixel_y: float) -> Optional[Tuple[float, float]]:
        # Return None if homography matrix is not loaded
        if self.homography_matrix is None:
            print("Warning: Homography matrix not loaded. Run calibration first.")
            return None
        
        # Undistort point if intrinsics are available
        if self.camera_matrix is not None and self.dist_coeffs is not None:
            pixel_x, pixel_y = self.undistort_point(pixel_x, pixel_y)
        
        # Apply homography transformation
        pixel_point = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
        robot_point = cv2.perspectiveTransform(pixel_point, self.homography_matrix)
        
        # Return the robot world coordinates
        robot_x = float(robot_point[0][0][0])
        robot_y = float(robot_point[0][0][1])
        return robot_x, robot_y
    

    # Undistort an entire image using intrinsic calibration
    def undistort_image(self, image: np.ndarray) -> np.ndarray:
        # Return original if not calibrated
        if self.camera_matrix is None or self.dist_coeffs is None:
            return image
        
        # Get the optimal new camera matrix
        h, w = image.shape[:2]
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
            self.camera_matrix, self.dist_coeffs, (w, h), 1, (w, h)
        )
        # Undistort the image
        undistorted = cv2.undistort(image, self.camera_matrix, self.dist_coeffs, 
                                    None, new_camera_matrix)
        return undistorted


# Convenience functions for standalone usage
def calibrate_intrinsics(stream_url: str, 
                        checkerboard_size: Tuple[int, int] = (9, 6),
                        square_size_mm: float = 20.0,
                        num_images: int = 20) -> bool:
    # Calibrate the camera intrinsics
    calibrator = CameraCalibrator()
    return calibrator.calibrate_intrinsics(stream_url, checkerboard_size, 
                                          square_size_mm, num_images)


# Calibrate the coordinate transformation
def calibrate_coordinate_transform(stream_url: str, min_points: int = 4) -> bool:
    # Calibrate the coordinate transformation
    calibrator = CameraCalibrator()
    return calibrator.calibrate_coordinate_transform(stream_url, min_points)


# Transform pixel coordinates to robot world coordinates
def pixel_to_robot(pixel_x: float, pixel_y: float) -> Optional[Tuple[float, float]]:
    # Load the calibration
    calibrator = CameraCalibrator()
    calibrator.load_calibration()
    # Return the robot world coordinates
    return calibrator.pixel_to_robot(pixel_x, pixel_y)


if __name__ == "__main__":
    
    print("\nCamera Calibration Module")
    print("\n1. Calibrate intrinsic parameters (checkerboard)")
    print("2. Calibrate coordinate transformation (click points)")
    print("3. Test pixel to robot transformation")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    calibrator = CameraCalibrator()
    
    if choice == "1":
        # Intrinsic calibration
        checkerboard_size = (9, 6)  # Adjust based on your checkerboard
        square_size = 20.0  # Size in mm
        calibrator.calibrate_intrinsics(STREAM_URL, checkerboard_size, square_size)
    
    elif choice == "2":
        # Coordinate transformation calibration
        calibrator.calibrate_coordinate_transform(STREAM_URL)
    
    elif choice == "3":
        # Test transformation
        calibrator.load_calibration()
        
        # Test with live camera feed
        cap = cv2.VideoCapture(STREAM_URL)
        if cap.isOpened():
            print("\nClick on image to see robot coordinates. Press 'q' to quit.")
            
            # Mouse callback for testing the transformation
            def test_click(event, x, y, flags, param):
                if event == cv2.EVENT_LBUTTONDOWN:
                    robot_coords = calibrator.pixel_to_robot(x, y)
                    if robot_coords:
                        print(f"Pixel ({x}, {y}) -> Robot ({robot_coords[0]:.1f}, {robot_coords[1]:.1f}) mm")
            
            # Test the transformation
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Undistort if intrinsics available
                if calibrator.camera_matrix is not None:
                    frame = calibrator.undistort_image(frame)
                
                # Display the frame with the transformation
                cv2.imshow("Test Transformation (click to test)", frame)
                cv2.setMouseCallback("Test Transformation (click to test)", test_click)
                
                # Wait for user input
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
            # Release the camera and close the window
            cap.release()
            cv2.destroyAllWindows()
        else:
            print("Error: Could not open camera stream")
    
    else:
        print("Exiting...")

