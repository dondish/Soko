# Soko
Easy to learn python music bot that has many features.

Add this bot to your server via this link (change the id to your bots id): https://discordapp.com/api/oauth2/authorize?client_id=INSERT-ID-HERE&permissions=3230720&scope=bot

# FAQ
* Q: How do I change the presence of the bot?
* A: Go to events.py and edit the bot.change_presence in the setup function.



* Q: How do I change the help function?
* A: Go to run.py and edit the Format class, please make sure you won't break the bot.



* Q: Can I have guild specific profile picture?
* A: Sadly Discord doesn't allow guild specific profile pictures.


# Requirements
1. Lavalink server

2. A little bit of knowledge of Python

3. Minimal knowledge of Discord.py to modify the bot

# Setup
1. Clone the repository to your preferred folder

2. Install Lavalink - more info about Lavalink here: https://github.com/Frederikam/Lavalink

3. Follow the server configuration tutorial in the link above and add to config.py the password, websocket url and the rest url.

4. Create a discord app go to here: https://discordapp.com/developers/applications/me and create a new app. 
Make sure you press create a bot user down below, like this:

![Create a bot user](http://donbot.space/i/9ef678a.PNG)

5. Copy the token from your app and paste it in config.py where the token needs to be. You can also make your bot public. DO NOT PUBLISH THE TOKEN ANYWHERE.

![token](http://donbot.space/i/a2c10d1.PNG)

6. Change OWNER_NAME to your username + discriminator (dondish#7155) and change OWNER_ID to your user id, you can find it by enabling developer mode in discord settings and right clicking on your account.
Full steps how to find your id here: https://support.discordapp.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-

7. Change the prefix and the description to something of your liking!

8. Done! your bot is ready to go! Run run.py and make sure the lavalink server is running!

# Support
Discord Server: https://discord.gg/hRSss
