**Instagram bot for like/follow/unfollow**
Simple bot that performs the above actions under your user

## Installation

1. Create file `common/settings.py` with content
	```
	from default_settings.py import *

	INSTA_USERS = {
		'USER_LOGIN': {
			'login': 'USER_LOGIN',
			'password': 'USER_PASSWORD',
			'likes_per_day': 1000,  # Defines intervals in secs for likes (1000 approx like in 1.5 minute)
			'follows_per_day': 100,  # Defines random range, when follow will be performed 100/1000 means one of 10
			'tags': ['London', 'NY', 'USA', 'England', 'Ireland', 'Miami', 'California']
		}
	}
	```
2. Install requirements
	```
	pip3 install -r requirements.txt
	```
3. Run bot in background
	```
	python3 manage.py run_bot -a USER_LOGIN &
	```

## Some thoughts
* Instagram mainly ban actions, not account
* Using more than 3000 likes per day causes frequent bans
