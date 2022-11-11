# The Unofficial GUI for the Unofficial TikTokApi

Provides a user friendly interface for the [Unofficial TikTok Api](https://github.com/davidteather/TikTok-Api). Allows you to download your liked videos, videos from the trending page, user uploads, and more.

<sup> Latest Update: **v0.7** New Tabs for byHashtag/bySearch, Bookmarks Page, Allows importing cookies as a workaround for current api bugs </sup>

**DISCLAIMER: The API that this was made for is very unstable so this project is mostly just here for showcasing at this point. Depending on the day it might actually work, so if you're really that interested in using this just contact me and I can help set it up. Most days it won't work though so I haven't put much effort into making this "ready for the public" yet** 

<sup>Also, I haven't cleaned up the code yet so don't judge me okay.. </sup>

![demo](https://github.com/DeeFrancois/tiktok-scraper-gui/blob/main/DocumentationImages/demo.gif)

## Motivation
I use TikTok for language learning and stumbled upon the very useful [Unofficial TikTok Api](https://github.com/davidteather/TikTok-Api) while looking for a way to download the videos. Figured it would be more efficient to use if it had an interface. Initially, I was just focused on downloading TikTok likes, but then I kept wanting to add more and more features to create a more complete and intuitive experience. I was also interested in getting experience with collaberating on a Github project, although I don't feel this is polished enough to share yet.

## External dependencies
- ffmpeg - https://www.ffmpeg.org/download.html
- mpv - https://github.com/jaseg/python-mpv
- youtube-dl - https://github.com/ytdl-org/youtube-dl

## Python dependencies
- opencv
- Pillow
- python-mpv
- TikTokApi
- youtube_dl

You can just use pip to install them with the requirements.txt file provided

## Importing your cookies

The API currently has a couple of bugs when it comes to the verification process during data fetching. However, they can be circumvented by providing your own cookies. To do this you will have to log in to the TikTok website, use a browser extension to export your cookies into a JSON file, and place that file in the same folder as the program. Doing this will also allow you to fetch your likes without having to make them public. 

Your JSON file should consist of a list of cookies formatted like so:
```
    {
    "domain": ".tiktok.com",
    "expirationDate": XXXXXXXXXXXXXXXX,
    "hostOnly": false,
    "httpOnly": false,
    "name": "passport_csrf_token",
    "path": "/",
    "sameSite": "no_restriction",
    "secure": true,
    "session": false,
    "storeId": "0",
    "value": "XXXXXXXXXXXXXXXXXXXXXXXXXX",
    "origin": "https://www.tiktok.com"
    },
```

## Usage

**Make sure your likes are public, enter your username in the top bar, click Retrieve TikToks**

<sup> *Retrievals are cached but the links expire after a day (?) so make sure you clear the cache eventually in order to get a fresh batch. </sup>

- Left Click to download (Powered by [ytdl](https://github.com/jaseg/python-mpv))
- Right Click to preview (Powered by [mpv](https://github.com/jaseg/python-mpv))

![demo](https://github.com/DeeFrancois/tiktok-scraper-gui/blob/main/DocumentationImages/leftrightClick.gif)

- If Selection Mode is enabled you can use Left Click to instead select which TikToks to download

![demo](https://github.com/DeeFrancois/tiktok-scraper-gui/blob/main/DocumentationImages/selectionMode.gif)

- Middle Click to get more info after the Extra Details sidebar is enabled
- Click on the User Avatar to open in your browser

![demo](https://github.com/DeeFrancois/tiktok-scraper-gui/blob/main/DocumentationImages/showDetails.gif)

- "Show Player" will open the Companion Video Player in another window for scrolling through downloaded videos

![demo](https://github.com/DeeFrancois/tiktok-scraper-gui/blob/main/DocumentationImages/showPlayer.gif)


Licensed under the [MIT License](LICENSE).
