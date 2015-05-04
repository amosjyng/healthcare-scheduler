import generate_patients as gp
from collections import deque
import pymc as mc
import sys

def time_str(time):
	return '%i:%02i' % (time/60, time % 60)

doctor_busy = False
wait_times = [0 for _ in range(gp.N_PATIENTS)]
idle_time = 0
overtime = 0


####### SCHEDULING
days = [{}]
day = 0 # current day, don't touch when scheduling!
t = 8*60 # current time, also don't touch!
appt_interval=10
def schedule_patient(patient):
        schedule_day = day
        schedule_time = t + appt_interval
        while True:
                schedule = days[schedule_day]
                while schedule_time < 18*60 - 20:
                        if schedule_time not in schedule:
                                schedule[schedule_time] = [patient]
                                return schedule_day, schedule_time
                        elif schedule_time == 8*60 and len(schedule[schedule_time]) < 2:
                                schedule[schedule_time].append(patient)
                                return schedule_day, schedule_time
                        schedule_time += appt_interval
                schedule_day += 1
                schedule_time = 8*60
                if len(days) == schedule_day:
                        days.append({})

for patient in gp.patients:
        schedule_patient(patient)
####### SCHEDULING


satisfied = [False for _ in gp.patients]
while not all(satisfied): # make sure all patients are seen
        print '----- 8 AM, START OF DAY {0} -----'.format(day)
        t = 8*60
        schedule = days[day]
        arrivals = {}
        departures = {}
        patient_queue = deque()
        while t < 18 * 60 or len(patient_queue) > 0 or len(departures) > 0:
                t_s = time_str(t)
                changed = False
                if t in schedule:
                        print '{0} -- {1} patients scheduled to arrive'.format(t_s, len(schedule[t]))
                        for patient in schedule[t]:
                                tard = gp.tardiness(patient, t).value
                                if (t+tard) not in arrivals:
                                        arrivals[t+tard] = []
                                if tard > 0:
                                        arrivals[t+tard].append((tard,patient))
                                elif tard == 0:
                                        print '{0} -- Patient {1} has arrived on time.'.format(t_s, patient[0])
                                        patient_queue.append(patient)
                                        changed = True
                                else:
                                        raise
                if t in arrivals:
                        for tard, patient in arrivals[t]:
                                if tard == 30:
                                        re_day, re_time = schedule_patient(patient)
                                        print '{0} -- Patient {1} not seen for half an hour, presumed no-show. Rescheduled for Day {2} at {3}'.format(t_s, patient[0], re_day, time_str(re_time))
                                else:
                                        print '{0} -- Patient {1} arrived {2} minutes late'.format(t_s, patient[0], tard)
                                        patient_queue.append(patient)
                                        changed = True
                if t in departures:
                        length, patient = departures[t]
                        print '{0} -- Doctor is finished with patient {2} after {1} minutes'.format(t_s, length, patient[0])
                        if satisfied[patient[0]]:
                                print 'ERROR -- Patient {0} is being seen a second time!'.format(patient[0])
                                sys.exit(1)
                        satisfied[patient[0]] = True
                        doctor_busy = False
                        del departures[t]
                if not doctor_busy:
                        if len(patient_queue) > 0:
                                patient = patient_queue.popleft()
                                print '{0} -- Doctor takes on patient {1}'.format(t_s, patient[0])
                                doctor_busy = True
                                length = gp.Poisson('appt_length', mu=20).value
                                departures[t+length] = (length,patient)
                                changed = True
                        else:
                                idle_time += 1
                for patient in patient_queue:
                        wait_times[patient[0]] += 1
                if changed:
                        print 'Queue now has {0} patients waiting'.format(len(patient_queue))
                if t >= 18*60:
                        overtime += 1
                t += 1
        print '----- {0}, END OF DAY {1} -----'.format(time_str(t), day)
        day += 1

total_wait = sum(wait_times)
print '\nDoctor idle time = {0}, doctor overtime = {1}, total patient wait time = {2}, final cost = {3}'.format(idle_time, overtime, total_wait, overtime * 20 + 10 * idle_time + total_wait)
