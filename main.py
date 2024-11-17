import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
import cv2 as cv
import numpy as np
import winsound
import sys

class Panorama(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('파노라마 영상 생성기')
        self.setGeometry(200, 200, 800, 300)
        self.setStyleSheet("background-color: #f0f0f0;")

        # 중앙 위젯 생성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        # 버튼 스타일
        button_style = """
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """

        # 버튼 생성 및 스타일 적용
        self.collectButton = QPushButton('영상 수집', self)
        self.showButton = QPushButton('영상 보기', self)
        self.stitchButton = QPushButton('봉합', self)
        self.saveButton = QPushButton('저장', self)
        quitButton = QPushButton('나가기', self)

        buttons = [self.collectButton, self.showButton, self.stitchButton, self.saveButton, quitButton]
        for button in buttons:
            button.setStyleSheet(button_style)
            button_layout.addWidget(button)

        # 레이블 생성 및 스타일 적용
        self.label = QLabel('환영합니다!', self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border: 2px solid #dddddd;
                border-radius: 10px;
                padding: 10px;
                font-size: 18px;
            }
        """)

        # 레이아웃에 위젯 추가
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.label)

        # 버튼 상태 설정
        self.showButton.setEnabled(False)
        self.stitchButton.setEnabled(False)
        self.saveButton.setEnabled(False)

        # 버튼 연결
        self.collectButton.clicked.connect(self.collectFunction)
        self.showButton.clicked.connect(self.showFunction)
        self.stitchButton.clicked.connect(self.stitchFunction)
        self.saveButton.clicked.connect(self.saveFunction)
        quitButton.clicked.connect(self.quitFunction)

        self.cap = None
        self.imgs = []
        self.img_stitched = None
        
    def collectFunction(self):
        self.showButton.setEnabled(False)
        self.stitchButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.label.setText('c를 여러 번 눌러 수집하고 끝나면 q를 눌러 비디오를 끕니다.')
        
        self.cap = cv.VideoCapture(0, cv.CAP_DSHOW)
        if not self.cap.isOpened(): 
            self.label.setText('카메라 연결 실패')
            return
        
        self.imgs = []
        while True:
            ret, frame = self.cap.read()
            if not ret: break
            
            cv.imshow('video display', frame)
            
            key = cv.waitKey(1)
            if key == ord('c'):
                self.imgs.append(frame)
            elif key == ord('q'):
                break
                
        self.cap.release()
        cv.destroyWindow('video display')
        
        if len(self.imgs) >= 2:
            self.showButton.setEnabled(True)
            self.stitchButton.setEnabled(True)
            self.saveButton.setEnabled(True)
            self.label.setText(f'{len(self.imgs)}장의 이미지가 수집되었습니다.')
        else:
            self.label.setText('최소 2장의 이미지가 필요합니다.')
            
    def showFunction(self):
        self.label.setText('수집된 영상은 '+str(len(self.imgs))+'장입니다.')
        if len(self.imgs) > 0:
            stack = cv.resize(self.imgs[0], dsize=(0,0), fx=0.25, fy=0.25)
            for i in range(1, len(self.imgs)):
                stack = np.hstack((stack, cv.resize(self.imgs[i], dsize=(0,0), fx=0.25, fy=0.25)))
            cv.imshow('Image collection', stack)
        else:
            self.label.setText('표시할 이미지가 없습니다.')
        
    def stitchFunction(self):
        if len(self.imgs) < 2:
            self.label.setText('파노라마를 만들기 위해서는 최소 2장의 이미지가 필요합니다.')
            return
        
        stitcher = cv.Stitcher_create()
        status, self.img_stitched = stitcher.stitch(self.imgs)
        if status == cv.STITCHER_OK:
            cv.imshow('Image stitched panorama', self.img_stitched)
            self.label.setText('파노라마가 성공적으로 생성되었습니다.')
        else:
            winsound.Beep(3000,500)
            self.label.setText('파노라마 제작에 실패했습니다. 다시 시도하세요.')
            self.img_stitched = None
            
    def saveFunction(self):
        if self.img_stitched is None:
            self.label.setText('저장할 파노라마 이미지가 없습니다.')
            return
        
        try:
            fname = QFileDialog.getSaveFileName(self, '파일 저장', './', 'Images (*.jpg *.png);;All Files (*)')
            
            if fname[0]:
                # 파일 경로를 UTF-8로 디코딩
                save_path = os.path.abspath(fname[0])
                save_path = save_path.encode('utf-8').decode('utf-8')

                if not save_path.lower().endswith(('.jpg', '.png')):
                    save_path += '.jpg'
                
                # OpenCV의 imwrite 대신 imencode와 파일 쓰기 사용
                is_success, im_buf_arr = cv.imencode(".jpg", self.img_stitched)
                if is_success:
                    with open(save_path, 'wb') as f:
                        im_buf_arr.tofile(f)
                    self.label.setText('파일이 성공적으로 저장되었습니다.')
                else:
                    self.label.setText('파일 저장에 실패했습니다.')
        except Exception as e:
            self.label.setText(f'저장 중 오류가 발생했습니다: {str(e)}')
        
    def quitFunction(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        cv.destroyAllWindows()
        self.close()
        
app = QApplication(sys.argv)
win = Panorama()
win.show()
app.exec_()