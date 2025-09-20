# Discord-Message-React
Simple Discord Message reaction self bot with custom emojis, channels and per user rules


This python scripts operates on boring http requests so you don't need to worry about having discord-self.py

Simply provide USER_TOKEN in .env file with rest of needed informations such as:
CHANNEL_IDS=ID's of channel separated with "," example =345346563654645,54654654645645645

REACTIONS=Reactions in unicode format to be used, separated by ","

Random delay range in seconds, between adding reactiosn (to avoid rate limiting)

CHECK_INTERVAL= In seconds, how offten code should check channels for new messages.
  Code have queue system. Explanation: If someone / couple users spam messages fast (faster than set CHECK_INTERVAL time)
  script will catch all new messages after last one it reacted to, put them in queue and add reactions to every one of them with respecting delay settings.

In default mode, code catch all messages from everyone and add selected emojis to them, but you can specify emomjis per user.
Explanation:
  AUTHOR_FILTERS= empty will cause code to use default emojis to react to all messages

  AUTHOR_FILTERS=1140374888899717260:🇩🇪|987698979098765432:sampleemoji 
  Will result in specified users messages to be reacted only with "🇩🇪" and "sampleemoji" emoji (you can separate emojis with "," to add multiple of them) for rest messages will be used defaukt reaction from REACTION=
  
  AUTHOR_FILTERS=1140374888899717260:🇩🇪|987698979098765432:sampleemoji
  REACTIONS=
  Will result in only specified users messages to be reacted to. Rest of users will be ignored.
If you do not want use this functions or part of it, just simply put "#" on the beginning of line.
Exampple:
# AUTHOR_FILTERS= will cause code to ignore this function even If you already added here some IDs, and work in default mode.

You can specify many channels IDs and users IDs but dont make it too much, http request spam can trigger reate limiting (or just make random delay seconds higher)
