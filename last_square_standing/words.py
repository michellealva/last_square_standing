# Copyright (c) 2024, Michelle and contributors
"""Built-in word bank for themed rounds.

Each round picks a category at random; its words label the grid tiles. The game
is still pure avoidance — the words are flavor, the prompt frames the round. Each
category must have at least 25 words so it can fill the largest (5x5) grid.
"""

import random

# (category, prompt, words)
WORD_BANK = [
	(
		"Cities",
		"Tap a city no one else will",
		[
			"Paris", "Tokyo", "Rome", "Cairo", "Lima", "Delhi", "Oslo", "Seoul",
			"Dubai", "Berlin", "Madrid", "Hanoi", "Quito", "Accra", "Dhaka",
			"Kyoto", "Lagos", "Miami", "Perth", "Vienna", "Nantes", "Bogota",
			"Athens", "Mumbai", "Boston", "Denver", "Havana", "Naples",
		],
	),
	(
		"Animals",
		"Tap an animal no one else will",
		[
			"Tiger", "Eagle", "Otter", "Panda", "Koala", "Zebra", "Camel", "Sloth",
			"Lemur", "Bison", "Moose", "Shark", "Whale", "Gecko", "Heron", "Raven",
			"Llama", "Hippo", "Rhino", "Viper", "Quail", "Mantis", "Falcon",
			"Badger", "Walrus", "Iguana", "Beaver", "Cheetah",
		],
	),
	(
		"Foods",
		"Tap a food no one else will",
		[
			"Pizza", "Sushi", "Tacos", "Pasta", "Curry", "Ramen", "Bagel", "Donut",
			"Mango", "Olive", "Pesto", "Gravy", "Toast", "Fries", "Melon", "Honey",
			"Waffle", "Cookie", "Pickle", "Cheese", "Mochi", "Falafel", "Burrito",
			"Noodle", "Pretzel", "Pancake", "Biscuit", "Muffin",
		],
	),
	(
		"Colors",
		"Tap a color no one else will",
		[
			"Crimson", "Indigo", "Amber", "Teal", "Coral", "Olive", "Maroon",
			"Violet", "Salmon", "Ivory", "Mauve", "Lilac", "Cyan", "Beige",
			"Khaki", "Plum", "Ruby", "Jade", "Pearl", "Slate", "Cobalt",
			"Scarlet", "Magenta", "Bronze", "Copper", "Emerald", "Saffron",
			"Lavender",
		],
	),
	(
		"Sports",
		"Tap a sport no one else will",
		[
			"Tennis", "Soccer", "Hockey", "Boxing", "Rugby", "Skiing", "Diving",
			"Rowing", "Karate", "Surfing", "Curling", "Cycling", "Fencing",
			"Sailing", "Archery", "Bowling", "Cricket", "Skating", "Hurdles",
			"Javelin", "Netball", "Polo", "Squash", "Judo", "Kayaking",
			"Climbing", "Sprinting", "Wrestling",
		],
	),
]


def pick_round(cells: int):
	"""Pick a random category and return (prompt, labels) where labels has exactly
	`cells` distinct words, one per tile."""
	category, prompt, words = random.choice(WORD_BANK)
	chosen = random.sample(words, cells)
	return prompt, chosen
