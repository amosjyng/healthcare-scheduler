from pymc import *
import numpy as np
from math import sqrt, exp, fabs

wealth_modifier = [0.2, 1.0, 1.5]

N_PATIENTS = 100


def will_go_rand(gender, age, wealth, preferred, appt_time):
	base_p = 0.8
	base_p *= wealth_modifier[wealth]
        base_p *= 1.5 / ((1 + fabs(1 + preferred - appt_time)) / 60.0)
	base_p *= (100 - age + 20) / 100.0
	base_p = pow(base_p, 1 / 10.0)
	return Bernoulli('w', p=base_p)

def will_go_logp(value, gender, age, wealth, preferred, appt_time):
	base_p = 0.5
	base_p *= wealth_modifier[wealth]
        base_p *= 1.5 / ((1 + fabs(1 + preferred - appt_time)) / 60.0)
	base_p *= (100 - age + 20) / 100.0
	base_p = pow(base_p, 1 / 10.0)
	return bernoulli_like(value, base_p)


def will_go_var(patient, appt_time):
        return Stochastic(name='will_go', doc='Does the patient decide to go?', parents = {'gender': patient[1], 'age' : patient[2], 'wealth': patient[3], 'preferred': patient[4], 'appt_time': appt_time}, random=will_go_rand, logp=will_go_logp, dtype=int)

def will_still_go_rand(will_go, wait_time):
        if will_go:
                if wait_time <= 20:
                        return 1
                else:
                        return Bernoulli('w', p=0.001)
        else:
                return 0

def will_still_go_logp(value, will_go, wait_time):
        if will_go:
                if wait_time <= 20:
                        return 0 if value == 1 else -np.inf
                else:
                        return bernoulli_like(value, 0.01)
        else:
                return 0 if value == 0 else -np.inf

def will_still_go_var(will_go, wait_time):
        return Stochastic(name='will_still_go', doc='Does the patient still want to go given the wait time?', parents = {'will_go': will_go, 'wait_time': wait_time}, random=will_still_go_rand, logp=will_still_go_logp, dtype=int)

def on_time_rand(gender, age, wealth, preferred, appt_time):
	base_p = 0.5
	base_p *= wealth_modifier[wealth]
        base_p *= 1.5 / ((1 + fabs(1 + preferred - appt_time)) / 60.0)
	base_p *= (100 - age + 20) / 100.0
	return Bernoulli('o', p=base_p)

def on_time_logp(value, gender, age, wealth, preferred, appt_time):
	base_p = 0.5
	base_p *= wealth_modifier[wealth]
        base_p *= 1.5 / ((1 + fabs(preferred - appt_time)) / 60.0)
	base_p *= (100 - age + 30) / 100.0
	return bernoulli_like(value, base_p)

def tardiness_rand(will_go, on_time):
	if will_go:
		if on_time:
			return 0
		else:
			return DiscreteUniform('t', lower=0, upper=20)
	else:
		return 30

def tardiness_logp(value, will_go, on_time):
	if will_go:
		if on_time:
			return 0 if value == 0 else -np.inf
		else:
			return discrete_uniform_like(value, 0, 20)
	else:
		return 0 if value == 30 else -np.inf

def tardiness(patient, appt_time, will_go=None):
        if will_go is None:
                will_go = will_go_var(patient, appt_time)
	on_time = Stochastic(name='on_time', doc='Does the patient come on time?', parents = {'gender': patient[1], 'age' : patient[2], 'wealth': patient[3], 'preferred': patient[4], 'appt_time': appt_time}, random=on_time_rand, logp=on_time_logp, dtype=int)
	return Stochastic(name='tardiness', doc='How late was the patient?', parents = {'will_go': will_go, 'on_time': on_time}, random=tardiness_rand, logp=tardiness_logp, dtype=int)

patients = np.ndarray(shape=(N_PATIENTS, 5), dtype=object)

for i in range(N_PATIENTS):
	patients[i][0] = i
	patients[i][1] = Bernoulli('gender_%i' % i, p=0.5)
	patients[i][2] = Normal('age_%i' % i, mu=40, tau=0.01)
	patients[i][3] = DiscreteUniform('wealth_%i' % i, lower=0, upper=2)
        patients[i][4] = DiscreteUniform('preferred_%i' % i, lower=8*60, upper=18*60-20)

if __name__ == '__main__':
	appointments = np.ndarray(shape=(N_PATIENTS, 2), dtype=object)
	for i in range(N_PATIENTS):
		appointments[i][0] = DiscreteUniform('appt_%i' % i, lower=8*60, upper=18*60-20)
		appointments[i][1] = tardiness(patients[i], appointments[i][0])
	numpy.savetxt('patients.csv', np.concatenate((patients[:,1:4], appointments), axis=1), fmt='%i', delimiter=',', header='gender,age,wealth,appointment time,tardiness')
