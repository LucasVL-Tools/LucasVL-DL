#!/usr/bin/env python3
from flask import Flask, request, render_template, redirect, abort, send_from_directory
import logging, os
from urllib import parse as urlparse
from yt_dlp import YoutubeDL as ydl
from waitress import serve
from config import (host, port, title, domain, unix_socket)

# Logging stuff for the waitress WSGI server
logging.basicConfig()
logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

# Starts the auto-deleter, done by forking the process and checking if the process is a parent or child. if process is child, run auto delete. if process is parent, run iapp.
#n = os.fork()
#if n > 0:
#    import auto_delete
#    while True: pass
#else: print("App started!")

app = Flask(__name__)
#app.config.update(
#    XCAPTCHA_SITE_KEY = captcha_site_key,
#    XCAPTCHA_SECRET_KEY = captcha_secret_key
#)
#if enable_captcha:
#    from flask_xcaptcha import XCaptcha
#    xcaptcha = XCaptcha(app=app, theme="dark")

# code i stole from stackoverflow
def video_id(value):
    """
    Examples:
    - http://youtu.be/SA2iWivDJiE
    - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    - http://www.youtube.com/embed/SA2iWivDJiE
    - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    """
    query = urlparse.urlparse(value)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = urlparse.parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    # fail?
    return None

# Code for serving home page
@app.route("/", methods=['GET'])
def home():
    return render_template("index.html", domain=domain, title=title)

# Code for video downloading
@app.route("/<v>", methods=['GET'])
@app.route("/v/<v>", methods=['GET'])
@app.route("/watch", methods=['GET'])
def dlvid(v=""):
    # compatibility for watch?v= yt links
    if not v: v = request.args.get("v")
    # if the user is tryna fuck with me, then i fuck with them
    if not v: v = "dQw4w9WgXcQ"

    if len(v) != 11:
        v = video_id(v)
        if not v:
            v = "dQw4w9WgXcQ"

    
    fileformat = request.args.get("format")
    
    if fileformat in ["opus", "mp3", "m4a", "wav", "flac", "avi", "webm", "wmv", "mov"]:
        fileext = fileformat
    else:
        fileext = "mp3"
    
    if fileext not in ["mp4", "mov", "wmv", "webm", "avi"]:
        args = {
                'format': 'bestaudio',
                'audio-format': fileext,
                'audio-quality': '0',
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': fileext}]
            }
    else: 
        args = {
                'format': 'best'
            }

    args.update({'outtmpl': f'./static/{fileext}/{v}.%(ext)s'})

    ydl(args).download(v)

    files = os.listdir(f"./static/{fileext}/")
    for l in files:
        if v == l[:11]:
            filename = l
            break
    return send_from_directory("static", f"{fileext}/{filename}", as_attachment = True)


###############
# ERROR PAGES #
###############

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', domain=domain, title="404 - page not found"), 404

# checks for unix socket or host in config file and runs waitress accordingly. 
"""
from werkzeug.middleware.profiler import ProfilerMiddleware
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[5], profile_dir="./profile")
app.run(debug = True)
"""

if host:
    serve(app, host=host, port=port)
elif unix_socket:
    serve(app, unix_socket=unix_socket, unix_socket_perms="777")
else: print("Please specify a host or unix socket (you probably just want host to be set to 0.0.0.0)")
