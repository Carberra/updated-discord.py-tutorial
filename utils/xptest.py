from random import randint

xp = 0
lvl = 0

for i in range(1000):
	xp += randint(10, 20)
	lvl = int((xp//42) ** 0.55)
	print(i+1, xp, lvl)