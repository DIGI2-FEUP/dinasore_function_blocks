class F_OR:

	def __init__(self):
		pass
		
	def schedule(self, event_input_name, event_input_value, IN1, IN2):

	EO_EVENT=True

	if(event_input_name == 'EI'):
		OUT = IN1 or IN2

	return [EO_EVENT, OUT]