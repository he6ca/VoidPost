# VOID//POST

A single-file web console for publishing text and photo posts to a Facebook Page you manage, using Facebook's official Graph API.

Made by **he6ća** · [t.me/he6ća](https://t.me/he6ća)

---

## What it does

- Connects to a Facebook Page with its Page ID and Page access token
- Tests the connection and shows the Page name before you post
- Saves the Page ID and token locally, so you don't have to re-enter them
- Composes up to 10 posts in one session, each with its own text
- Attaches a photo to any post, or posts text only
- Exchanges a short-lived token for a long-lived one
- Shows a confirmation dialog before publishing
- Logs every result, including the new post ID or the error message

Everything runs in one Python file (`voidpost.py`). The backend is Flask and the interface is a web page served from the same script.

---

## Requirements

- Python 3.9 or newer
- A Facebook Page you are an admin of
- A Facebook app with a Page access token that has the `pages_manage_posts` and `pages_read_engagement` permissions

---

## Installation

```bash
pip install flask requests
```

---

## Usage

1. Start the server:

   ```bash
   python voidpost.py
   ```

2. Open the console in your browser:

   ```
   http://127.0.0.1:5000
   ```

3. **Connect tab:** enter your Page ID and Page access token, then click **Test connection**. If it works, the status bar shows the Page name.
4. Optional: click **Save credentials** to keep the Page ID and token in a local config file.
5. **Compose tab:** choose how many posts to write (1 to 10). For each post, enter the text and tick **Include a photo** if you want one.
6. Click **Publish**, then confirm.
7. **Log tab:** see the result of each post, with the post ID or the error.

---

## How it works

**Frontend.** The HTML, CSS, and JavaScript are stored as one string inside `voidpost.py` and served at `/`. The page keeps the posts in memory and sends them to the backend when you publish.

**Backend routes:**

| Route | Purpose |
|---|---|
| `/` | Serves the console page |
| `/api/test-connection` | Calls `GET /{page-id}` on the Graph API to confirm the Page and token |
| `/api/save-credentials` | Writes the Page ID and token to a JSON config file |
| `/api/exchange-token` | Swaps a short-lived user token for a long-lived token |
| `/api/publish` | Publishes each post in order |

**Publishing.** For a text-only post, the backend calls `POST /{page-id}/feed`. For a post with a photo, it calls `POST /{page-id}/photos` with the image as the `source` file and the text as the `caption`. Posts go out one at a time, and each result is returned to the page.

**Config file.** Saved credentials are stored in `~/.fb_poster_gui_config.json`, outside the project folder.

---

## Security notes

- The server listens only on `127.0.0.1`, so only the computer running it can reach it.
- Tokens are stored in plain text in the config file. Keep that file private, and don't commit it to Git.
- Never share your access token or app secret. If one leaks, revoke it in the Meta developer dashboard.
- The tool uses only Facebook's official Graph API with a token you supply. It does not log in as a person or scrape anything.

---

## Limitations

- Facebook Page posting only. It doesn't post to personal profiles, groups, or Instagram.
- Posts go out one after another, and the run stops on the first error where possible. Facebook rate limits and spam filters can still reject posts.
- No scheduling. Posts publish immediately after confirmation.
- No login on the console itself, so keep it on your own machine.

---

## Project structure

```
voidpost.py    # backend, frontend, and everything else in one file
README.md
```

---

## License

Add your chosen license here (for example MIT).

---

## Disclaimer

This tool is not affiliated with Meta or Facebook. Use it only on Pages you manage and in line with Meta's Platform Terms and Community Standards.
