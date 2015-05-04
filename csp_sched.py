from generate_patients import *
from collections import deque
from pymc import *
from constraint import *

def time_str(time):
	return '%i:%02i' % (time/60, time % 60)

doctor_busy = False
wait_times = [0 for _ in range(N_PATIENTS)]
idle_time = 0


####### SCHEDULING
schedule = {}
##schedule[8*60] = [patients[0], patients[1]]
##for step in range(1, 600 / 20):
##	t = 8*60 + step * 20
##	schedule[t] = [patients[step + 1]]

## Extract Patient Preferences

## Use Model from Regression
for patient in patients
        L= -3.0541 + 0.4712*gender(patient)+ 0.0808*age(patient)-0.9001*wealth(patient)-0.1154*appttime(patient)
        Prediction[patient]=1/(1+e^-L)

## Use CSP
problem = Problem()
for patient in patients
        problem.addVariable("patientid", [preferred start])
problem.addConstraint()



####### SCHEDULING


arrivals = {}
departures = {}
patient_queue = deque()
t = 8*60
while t < 18 * 60 or len(patient_queue) > 0:
	t += 1
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
		print '{0} -- Doctor is finished with a patient after {1} minutes'.format(t_s, departures[t])
		doctor_busy = False
	if not doctor_busy:
		if len(patient_queue) > 0:
			patient = patient_queue.popleft()
			print '{0} -- Doctor takes on patient {1}'.format(t_s, patient[0])
			doctor_busy = True
			length = Poisson('appt_length', mu=20).value
			departures[t+length] = length
			changed = True
		else:
			idle_time += 1
	for patient in patient_queue:
		wait_times[patient[0]] += 1
	if changed:
		print 'Queue now has {0} patients waiting'.format(len(patient_queue))

total_wait = np.array(wait_times).sum()
print '\nDoctor idle time = {0}, total patient wait time = {1}, final cost = {2}'.format(idle_time, total_wait, 10 * idle_time + total_wait)
