########################################
#Top of file
#Gift Card Generator
#
#
########################################
__author__ = 'Cruor'
import string
import random



	
def phrasegen(chars=string.ascii_uppercase + string.digits, size=6):
		randomized = ''.join(random.choice(chars) for _ in range(size))
		print 'Gameserver-'+randomized
		return 'Gameserver-'+randomized





		