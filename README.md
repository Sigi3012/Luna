<div align=center>
  <h1>A simple Discord embed fixer </h1>
    <a href="https://github.com/Sigi3012/EmbedFixer/stargazers" target="_blank">
      <img alt="stars" src="https://img.shields.io/github/stars/sigi3012/embedfixer" />
    </a>
    <a href="https://github.com/Sigi3012/embedFixer/blob/main/LICENSE" target="_blank">
    <img alt="license" src="https://img.shields.io/github/license/Sigi3012/EmbedFixer" />
   </a>
</div>

---

This bot automaticaly fixes [Twitter](https://twitter.com) (or [X.com](https://x.com)), [Instagram](https://instagram.com), [TikTok](https://tiktok.com) or [Reddit](https://reddit.com) links

### Commands:
1. /toggle
2. /status
3. /shutdown

If you only care about the link fixer use branch [lightweight](https://github.com/Sigi3012/embedFixer/tree/lightweight)

## Installation
### Requirements
* Python3.11 or higher <br> (lower versions untested)
* Discord.py
```sh
git clone https://github.com/Sigi3012/embedFixer
cd embedFixer
```
### Docker
* Install [Docker](https://docs.docker.com/desktop/release-notes/)
* Edit the "docker-compose.yml" and add your bot's token and your personal userid to the respective values under "environment:"
```sh
docker compose up # Add "-d" to run detached
```
### Local
You don't need to edit .env just run and follow install script
```sh
pip install -r requirements.txt

# Windows
python main.py
# Unix
python3 main.py
```
```sh
# If you dont want to install globally

# Windows
python -m venv venv
.\venv\Scripts\activate
# Unix
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```
### Server
```sh
pip install -r requirements.txt

sudo apt get tmux # Or whatever package manager you use
tmux
python3 main.py
CTRL+B > d

# Reattach with 
tmux attach-session
```

## Credits ❤️

Please go and star these repos, as this project wouldn't be possible without them

[FixTweet](https://github.com/FixTweet/FixTweet) \
[Instafix](https://github.com/Wikidepia/InstaFix) \
[vxtiktok](https://github.com/dylanpdx/vxtiktok) \
[FixReddit](https://github.com/MinnDevelopment/fxreddit)

## TODO
1. Better logging
2. Pinterest fix (never)
3. <s>Move to cogs</s>
4. <s>More platforms</s>

---

