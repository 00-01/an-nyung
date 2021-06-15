import multiprocessing
import threading
import time
import concurrent.futures as cf
import cv2
import face_recognition as fr
import numpy as np
from db import access_db
from multiprocessing import Process, Queue

_, _, col, error_col = access_db()
n = list(col.find({}))
names = [i['name'] for i in n]
id = [j['id'] for j in n]
cam_num = '0'
cap = cv2.VideoCapture(0)
distance = 0.4

cap_size = (300, 300)



def test1(q):
	while True:
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
					

def run():
	s = time.time()
	while True:
		ret, frame = cap.read()
		frame = cv2.flip(frame, 1)
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
		# cv2.imshow('frame_m', frame[int(frame.shape[0] / 2 - cap_size[0] / 2): int(frame.shape[0] / 2 + cap_size[0] / 2),
		# 				int(frame.shape[1] / 2 - cap_size[1] / 2): int(frame.shape[1] / 2 + cap_size[1] / 2)])

		# ROI사각형
		cv2.rectangle(frame,
					  (int(frame.shape[1] / 2 - cap_size[1] / 2), int(frame.shape[0] / 2 - cap_size[0] / 2)),
					  (int(frame.shape[1] / 2 + cap_size[1] / 2), int(frame.shape[0] / 2 + cap_size[0] / 2)),
					  (0, 0, 255), 2)
		# fps출력
		cv2.putText(frame, "fps : " + fps, (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)


		cv2.imshow('frame', frame)
		if cv2.waitKey(1) == 27:
			for pp in pro_list:
				pp.kill()
			break

pro_list = []
if __name__ == '__main__':
	q = Queue()
	for _ in range(multiprocessing.cpu_count() - 1):
		p = Process(target=test1, args=(q,))
		pro_list.append(p)
		p.start()
		time.sleep(float(1) / (multiprocessing.cpu_count() - 2))
	run()

