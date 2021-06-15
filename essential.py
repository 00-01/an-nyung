import json
import multiprocessing
import threading
import time
import concurrent.futures as cf
import cv2
import face_recognition as fr
import numpy as np
from db import access_db
from multiprocessing import Process, Queue
import platform



with open('config.json') as json_file:
    setting = json.load(json_file)

_, _, col, error_col = access_db()
n = list(col.find({}))
names = [i['name'] for i in n]
id = [j['id'] for j in n]

cam_dev = 0
cam_cap = 0
for s_os in setting["camera"]["os"]:
	if s_os in platform.platform():
		cam_num = setting["camera"]["os"][s_os]["dev"]
		cam_cap = setting["camera"]["os"][s_os]["cap"]
		break
# print(platform.platform())
cap = cv2.VideoCapture(cam_num, cam_cap)
distance = setting["distance"]

cap_size = (setting["camera"]["roi"]["width"], setting["camera"]["roi"]["height"])

pro_list = []



def image_anlyize(q):
	while True:
		# 큐에 있는 frame가져와서 face_location처리
		if q:
			frame = q.get()
			face_locations = fr.face_locations(frame)
			if face_locations :
				face_encodings = fr.face_encodings(frame, face_locations)

				for (y, x1, y1, x), face_encoding in zip(face_locations, face_encodings):
					name = "- - -"
					face_distances = fr.face_distance(id, face_encoding)
					best_match_index = np.argmin(face_distances)
					if face_distances[best_match_index] < distance:
						name = names[best_match_index]
					print(name)
					

def capture():
	s = time.time()
	while True:
		ret, frame = cap.read()
		frame = cv2.flip(frame, 1)
		# cpu 코어 갯수 - 2개 만큼만 face_recognition돌림
		# capture돌아가는 1개
		# 여유분 1개
		if q.qsize() < multiprocessing.cpu_count() - 2:
			seconds = time.time() - s
			if seconds > float(1) / (multiprocessing.cpu_count() - 2):
				s = time.time()
				# ROI
				# 중앙에서 cap_size만큼
				q.put(frame[int(frame.shape[1] / 2 - cap_size[1] / 2): int(frame.shape[1] / 2 + cap_size[1] / 2),
						int(frame.shape[0] / 2 - cap_size[0] / 2): int(frame.shape[0] / 2 + cap_size[0] / 2)])

		fps = 0
		try:
			pass
			# calculate fps
			fps = 1 / seconds
			fps = ("%.2f" % fps)
			# print(f"fps : {fps}", '\n')
		except:
			pass

		# ROI
		if setting["view"]["roi"]:
			cv2.imshow('roi', frame[int(frame.shape[0] / 2 - cap_size[0] / 2): int(frame.shape[0] / 2 + cap_size[0] / 2),
							int(frame.shape[1] / 2 - cap_size[1] / 2): int(frame.shape[1] / 2 + cap_size[1] / 2)])

		# ROI사각형
		cv2.rectangle(frame,
					  (int(frame.shape[1] / 2 - cap_size[1] / 2), int(frame.shape[0] / 2 - cap_size[0] / 2)),
					  (int(frame.shape[1] / 2 + cap_size[1] / 2), int(frame.shape[0] / 2 + cap_size[0] / 2)),
					  (0, 0, 255), 2)
		# fps출력
		if setting["view"]["fps"]:
			cv2.putText(frame, "fps : " + fps, (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)


		cv2.imshow('frame', frame)


		if cv2.waitKey(1) == 27:
			for pp in pro_list:
				pp.kill()
			cap.release()
			cv2.destroyAllWindows()
			return

if __name__ == '__main__':
	q = Queue()
	for _ in range(multiprocessing.cpu_count() - 1):
		p = Process(target=image_anlyize, args=(q,))
		pro_list.append(p)
		p.start()
		time.sleep(float(1) / (multiprocessing.cpu_count() - 2))
	capture()

