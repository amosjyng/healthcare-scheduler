import generate_patients as gp
from collections import deque
import pymc as mc
import sys
import constraint
import math

def time_str(time):
	return '%i:%02i' % (time/60, time % 60)

doctor_busy = False
wait_times = [0 for _ in range(gp.N_PATIENTS)]
idle_time = 0


####### SCHEDULING
days = [{}]
day = 0 # current day, don't touch when scheduling!
t = 8*60 # current time, also don't touch!
def get_pref_times(patient, max_day):
        times = []
        preferred = (patient[4] - 8*60) / 10
        preferred = preferred * 10 + 8*60
        for sched_day in range(day, max_day + 1):
                begin_time = preferred - 20
                begin_time = begin_time if begin_time >= 8*60 else 8*60
                end_time = preferred + 20
                end_time = end_time if end_time <= 18*60-20 else 18*60-20
                for sched_time in range(begin_time, end_time + 1, 10):
                        times.append((sched_day, sched_time))
        return times

def schedule_patient(patient):
        schedule_day = day
        schedule_time = t + 10
        while True:
                schedule = days[schedule_day]
                while schedule_time < 18*60 - 20:
                        if schedule_time not in schedule:
                                schedule[schedule_time] = [patient]
                                return schedule_day, schedule_time
                        schedule_time += 10
                schedule_day += 1
                schedule_time = 8*60
                if len(days) == schedule_day:
                        days.append({})

max_sched_days = int(math.ceil(gp.N_PATIENTS / (10 * 3.0)))
while max_sched_days >= len(days):
        days.append({})
times = set()
for patient in gp.patients:
        found = False
        for pref in get_pref_times(patient, max_sched_days - 1):
                if pref not in times:
                        found = True
                        sched_day, sched_time = pref
                        
                        days[sched_day][sched_time] = [patient]
                        times.add(pref)
                        break
        if not found:
                print patient[0]
                sched_day, sched_time = schedule_patient(patient)
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
                t += 1
        print '----- {0}, END OF DAY {1} -----'.format(time_str(t), day)
        print satisfied
        day += 1

total_wait = sum(wait_times)
print '\nDoctor idle time = {0}, total patient wait time = {1}, final cost = {2}'.format(idle_time, total_wait, 10 * idle_time + total_wait)
