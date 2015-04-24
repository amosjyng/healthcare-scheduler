from pymc import DiscreteUniform

appointment_time = DiscreteUniform('appt time', lower=8, upper=17, doc='Appointment time in 24 hour clock')

print appointment_time.value
