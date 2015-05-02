from pymc import *
import numpy as np
from math import sqrt

wealth_modifier = [0.2, 1.0, 1.5]

N_PATIENTS = 100


def remembered_rand(gender, age, wealth, appt_time):
	base_p = 0.8
	base_p *= wealth_modifier[wealth]
	base_p *= (appt_time / 60 - 8 + 2) / 10.0
	base_p *= (100 - age + 20) / 100.0
	base_p = pow(base_p, 1 / 10.0)
	return Bernoulli('r', p=base_p)

def remembered_logp(value, gender, age, wealth, appt_time):
	base_p = 0.5
	base_p *= wealth_modifier[wealth]
	base_p *= (appt_time / 60 - 8 + 2) / 10.0
	base_p *= (100 - age + 20) / 100.0
	base_p = pow(base_p, 1 / 10.0)
	return bernoulli_like(value, base_p)

def on_time_rand(gender, age, wealth, appt_time):
	base_p = 0.5
	base_p *= wealth_modifier[wealth]
	base_p *= (appt_time / 60 - 8 + 2) / 10.0
	base_p *= (100 - age + 20) / 100.0
	return Bernoulli('o', p=base_p)

def on_time_logp(value, gender, age, wealth, appt_time):
	base_p = 0.5
	base_p *= wealth_modifier[wealth]
	base_p *= (appt_time / 60 - 8 + 2) / 10.0
	base_p *= (100 - age + 30) / 100.0
	return bernoulli_like(value, base_p)

def tardiness_rand(remembered, on_time):
	if remembered:
		if on_time:
			return 0
		else:
			return DiscreteUniform('t', lower=0, upper=20)
	else:
		return 30

def tardiness_logp(value, remembered, on_time):
	if remembered:
		if on_time:
			return 0 if value == 0 else -np.inf
		else:
			return discrete_uniform_like(value, 0, 20)
	else:
		return 0 if value == 30 else -np.inf

def tardiness(patient, appt_time):
	remembered = Stochastic(name='remembered', doc='Did the patient remember?', parents = {'gender': patient[1], 'age' : patient[2], 'wealth': patient[3], 'appt_time': appt_time}, random=remembered_rand, logp=remembered_logp, dtype=int)
	on_time = Stochastic(name='on_time', doc='Did the patient come on time?', parents = {'gender': patient[1], 'age' : patient[2], 'wealth': patient[3], 'appt_time': appt_time}, random=on_time_rand, logp=on_time_logp, dtype=int)
	return Stochastic(name='tardiness', doc='How late was the patient?', parents = {'remembered': remembered, 'on_time': on_time}, random=tardiness_rand, logp=tardiness_logp, dtype=int)

patients = np.ndarray(shape=(N_PATIENTS, 4), dtype=object)

for i in range(N_PATIENTS):
	patients[i][0] = i
	patients[i][1] = Bernoulli('gender_%i' % i, p=0.5)
	patients[i][2] = Normal('age_%i' % i, mu=40, tau=0.01)
	patients[i][3] = DiscreteUniform('wealth_%i' % i, lower=0, upper=2)

if __name__ == '__main__':
	appointments = np.ndarray(shape=(N_PATIENTS, 2), dtype=object)
	for i in range(N_PATIENTS):
		appointments[i][0] = DiscreteUniform('appt_%i' % i, lower=8*60, upper=18*60)
		appointments[i][1] = tardiness(patients[i], appointments[i][0])
	numpy.savetxt('patients.csv', np.concatenate((patients[:,1:4], appointments), axis=1), fmt='%i', delimiter=',', header='gender,age,wealth,appointment time,tardiness')
