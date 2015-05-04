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
overtime = 0


####### SCHEDULING
days = [{}]
day = 0 # current day, don't touch when scheduling!
t = 8*60 # current time, also don't touch!
appt_interval=10
def get_pref_times(patient, max_day):
        times = []
        preferred = (patient[4] - 8*60) / appt_interval
        preferred = preferred * appt_interval + 8*60
        for sched_day in range(day, max_day + 1):
                begin_time = preferred - 20
                begin_time = begin_time.value if begin_time.value >= (8*60) else (8*60)
                end_time = preferred + 20
                end_time = end_time if end_time <= 18*60-20 else 18*60-20
                for sched_time in range(begin_time, end_time + 1, appt_interval):
                        times.append((sched_day, sched_time))
        return times

def schedule_patient(patient):
        schedule_day = day
        schedule_time = t + appt_interval
        while True:
                schedule = days[schedule_day]
                while schedule_time <= 18*60 - 20:
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

max_sched_days = int(math.ceil(gp.N_PATIENTS / (10 * 60 / float(appt_interval))))
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
                times.add(schedule_patient(patient))
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
                if t+30 in schedule:
                        estimated_wait = len(patient_queue) * 20
                        for future_patient in schedule[t+30]:
                                wg = gp.will_go_var(future_patient, t+30)
                                if gp.will_still_go_var(wg, estimated_wait).value == 0:
                                        resched_day, resched_time = schedule_patient(future_patient)
                                        print 'Due to long wait times, Patient {0} is rescheduled to arrive at {1} on day {2} instead of {3} today'.format(future_patient[0], time_str(resched_time), resched_day, time_str(t+30))
                                        schedule[t+30].remove(future_patient)
                                else:
                                        tard = gp.tardiness(patient, t, wg).value
                                        if (t+tard+30) not in arrivals:
                                                arrivals[t+30+tard] = []
                                        arrivals[t+30+tard].append((tard, future_patient))
                                        if tard == 30:
                                                print 'WTF'
                                                sys.exit(1)
                                        schedule[t+30].remove(future_patient)
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
                        print '{0} -- Doctor is finished with Patient {2} after {1} minutes'.format(t_s, length, patient[0])
                        if satisfied[patient[0]]:
                                print 'ERROR -- Patient {0} is being seen a second time!'.format(patient[0])
                                sys.exit(1)
                        satisfied[patient[0]] = True
                        doctor_busy = False
                        del departures[t]
                if not doctor_busy:
                        if len(patient_queue) > 0:
                                patient = patient_queue.popleft()
                                print '{0} -- Doctor takes on Patient {1}'.format(t_s, patient[0])
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
