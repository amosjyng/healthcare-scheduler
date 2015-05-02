from generate_patients import *
from collections import deque
from pymc import *

def time_str(time):
	return '%i:%02i' % (time/60, time % 60)

appointment_length = Poisson('appt_length', mu=20)
doctor_busy = False

schedule = {}
schedule[8*60] = [patients[0], patients[1]]
for step in range(1, 10 * 6):
	t = 8*60 + step * 10
	schedule[t] = [patients[step + 1]]
arrivals = {}
departures = {}
patient_queue = deque()
for t in range(8*60, 20 * 60 + 1, 1):
	t_s = time_str(t)
	changed = False
	if t in schedule:
		print '{0} -- {1} patients scheduled to arrive'.format(t_s, len(schedule[t]))
		for patient in schedule[t]:
			tard = tardiness(patient, t).value
			if (t+tard) not in arrivals:
				arrivals[t+tard] = []

			if tard > 20:
				arrivals[t+tard].append((tard,None))
			elif 0 < tard <= 20:
				arrivals[t+tard].append((tard,patient))
			elif tard == 0:
				print '{0} -- Patient has arrived on time.'.format(t_s)
				patient_queue.append(patient)
				changed = True
			else:
				raise
	if t in arrivals:
		for tard, patient in arrivals[t]:
			if tard > 30 or patient is None:
				print '{0} -- Patient not seen for half an hour, presumed not to have arrived'.format(t_s)
			else:
				print '{0} -- Patient arrived {1} minutes late'.format(t_s, tard)
				patient_queue.append(patient)
				changed = True
	if t in departures:
		print '{0} -- Doctor is finished with a patient'.format(t_s)
		doctor_busy = False
	if not doctor_busy and len(patient_queue) > 0:
		print '{0} -- Doctor takes on a new patient'.format(t_s)
		patient_queue.popleft()
		doctor_busy = True
		departures[t+appointment_length.value] = 1
		changed = True
	if changed:
		print 'Queue now has {0} patients waiting'.format(len(patient_queue))
