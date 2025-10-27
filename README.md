# Discord-Message-React
Simple Discord Message reaction self bot with custom emojis, channels and per user rules.<br/><br/><br/>
## Features
- Operates on http requests so you don't need to worry about having discord-self.py
- Random delay range in seconds between reactions
- Queue system
- Anti rate limit
- Specify emoji per user or/and channel
- Ignore system<br/><br/><br/>
## Usage

Simply provide USER_TOKEN in **.env** file with rest of needed informations such as:<br/>
`CHANNEL_IDS=`ID's of channel separated with ","<br/>
>example =345346563654645,54654654645645645<br/>

`REACTIONS=`Reactions in unicode format to be used, separated by ","<br/><br/>

Random delay range in seconds, between adding reactions (to avoid rate limiting)<br/><br/>

`CHECK_INTERVAL=` In seconds, how offten code should check channels for new messages.
  >Code have queue system. Explanation: If someone / couple users spam messages fast (faster than set `CHECK_INTERVAL` time)
  >script will catch all new messages after last one it reacted to, put them in queue and add reactions to every one of them with respecting delay settings.<br/><br/>

In default mode, code catch all messages from everyone and add selected emojis to them, but you can specify emomjis per user.<br/>
Explanation:<br/>
  `AUTHOR_FILTERS=` empty will cause code to use default emojis to react to all messages

  `AUTHOR_FILTERS=USERID1:🇩🇪|USERID2:sampleemoji`<br/>
  >Will result in specified users messages to be reacted only with "🇩🇪" and "sampleemoji" emoji (you can separate emojis with "," to add multiple of them, and separate authors with **|**) for rest messages will be used defaukt reaction from `REACTION=`<br/>
  
  `AUTHOR_FILTERS=USERID1:🇩🇪|USERID2:sampleemoji`<br/>
  `REACTIONS=`<br/>
  >Will result in only specified users messages to be reacted to. Rest of users will be ignored.<br/>
If you do not want use this functions or part of it, just simply put **"#"** on the beginning of line.<br/>
Exampple:<br/>
`#AUTHOR_FILTERS=` will cause code to ignore this function even If you already added here some IDs, and work in default mode.<br/><br/>

You can specify many channels IDs and users IDs but dont make it too much, http request spam can trigger reate limiting (or just make random delay seconds higher)
