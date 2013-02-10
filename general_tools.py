'''
Created on Feb 1, 2013

	general_tools.py is a list of support functions logging
	and printing to the terminal

@author: jparrella
'''
import math

def print_place(module, str_out):
	print module, ": ", str_out

def dotproduct(v1, v2):
	return sum((a*b) for a, b in zip(v1, v2))

def length(v):
	return math.sqrt(dotproduct(v, v))

def cos_angle(v1, v2):
	if (length(v1) * length(v2)) == 0:
		denom = 1.0
	else:
		denom = (length(v1) * length(v2))

	return dotproduct(v1, v2) / denom

