# The Unofficial GUI for the Unofficial TikTokApi

Provides a user friendly interface for the [Unofficial TikTok Api](https://github.com/davidteather/TikTok-Api). Allows you to download your liked videos, videos from the trending page, user uploads, and more.

<sup> Latest Update: **v0.7** New Tabs for byHashtag/bySearch, Bookmarks Page, Allows importing cookies as a workaround for current api bugs </sup>

<sup> Disclaimer: Atleast until v1.0, this is mostly here for showcasing. But if you would like to use it, just contact me and I can help you get it working on your machine (mpv installation is a bit tricky). </sup>

![demo](https://github.com/DeeFrancois/tiktok-scraper-gui/blob/main/DocumentationImages/demo.gif)

#### *Currently only works if you input your own cookies after logging into the TikTok website. Once I can automate this process, I will release it as an exe*


## Motivation
I use TikTok for language learning and stumbled upon the very useful [Unofficial TikTok Api](https://github.com/davidteather/TikTok-Api) while looking for a way to download the videos. I figured I could utilize it more efficiently if it had an interface. I was initially focused on just downloading TikTok likes, but then I kept wanting to add more and more features to create a more complete and intuitive experience. I was also interested in getting experience with collaberating on a Github project, although I don't feel this is polished enough to share yet.

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
