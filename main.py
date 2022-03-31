from flask import Flask, jsonify, url_for, make_response, request, render_template, send_from_directory
import requests, os, re
from html_to_json import convert as html_to_json

app = Flask(__name__)

def normal_user_to_partial_user(user):
    return {
      "username": user["username"],
      "id": user["id"],
      "image_id": user["profile"]["id"]
    }
  
def render_comment_from_html(comment):
  try:
    comment["ul"][0]["li"]
  except KeyError:
    try:
      comment["div"][0]["div"][1]["div"][1]["_value"]
    except KeyError:
      return {
        "id": int(comment["div"][0]["_attributes"]["data-comment-id"]),
        "username": comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
        "comment": "",
        "replies": []
      }
    else:
      return {
        "id": int(comment["div"][0]["_attributes"]["data-comment-id"]),
        "username": comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
        "comment": comment["div"][0]["div"][1]["div"][1]["_value"],
        "replies": []
      }
  else:
    replies = []
    for reply_comment in comment["ul"][0]["li"]:
      try:
        reply_comment["div"][0]["div"][1]["div"][1]["_value"]
      except KeyError:
        replies.append({
          "id": int(reply_comment["div"][0]["_attributes"]["data-comment-id"]),
          "username": reply_comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
          "comment": ""
        })
      else:
        replies.append({
          "id": int(reply_comment["div"][0]["_attributes"]["data-comment-id"]),
          "username": reply_comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
          "comment": reply_comment["div"][0]["div"][1]["div"][1]["_value"]
        })
    try:
      comment["div"][0]["div"][1]["div"][1]["_value"]
    except KeyError:
      return {
        "id": int(comment["div"][0]["_attributes"]["data-comment-id"]),
        "username": comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
        "comment": "",
        "replies": replies
      }
    else:
      return {
        "id": int(comment["div"][0]["_attributes"]["data-comment-id"]),
        "username": comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
        "comment": comment["div"][0]["div"][1]["div"][1]["_value"],
        "replies": replies
      }

@app.route('/')
def home():
  r = make_response(render_template('home.html'), 200)
  return r

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/api/v1/')
def api():
  return jsonify({
    "home": url_for('home'),
    "docs": url_for('docs', version='v1')
  })

@app.route('/api/v1/users/<username>')
def user(username):
  if username.endswith("*"): username = username[:-1]
  res = requests.get(f"https://api.scratch.mit.edu/users/{username}")
  if request.args.get("nofollow") == None:
    following_res = requests.get(f"https://api.scratch.mit.edu/users/{username}/following").json()
    followers_res = requests.get(f"https://api.scratch.mit.edu/users/{username}/followers").json()
    following = []
    followers = []
    for follow in following_res:
      following.append(normal_user_to_partial_user(follow))
    for follow in followers_res:
      followers.append(normal_user_to_partial_user(follow))
  if request.args.get("noactivity") == None:
    pass
  if request.args.get("nostatus") == None:
    ocular_res = requests.get(f"https://my-ocular.jeffalo.net/api/user/{username}")
  if res:
    res = res.json()
    
    json = {
      "username": res["username"],
      "id": res["id"],
      "about": res["profile"]["bio"],
      "working_on": res["profile"]["status"],
      "scratch_team": res["scratchteam"],
      "image_id": res["profile"]["id"],
      "country": res["profile"]["country"],
      "join_date": res["history"]["joined"][:10],
      "join_time": res["history"]["joined"][11:-5]
    }
    if request.args.get("nofollow") == None:
      json["following"] = following
      json["followers"] = followers
    
    if request.args.get("nostatus") == None:
      ocular_res = ocular_res.json()
      json["status"] = ocular_res["status"]
      json["status_colour"] = ocular_res["color"]
    return jsonify(json)
  elif res.status_code == 404:
    return make_response(jsonify({
      "error": "User does not exist"
    }),404)
  else:
    return make_response(jsonify({
      "error": "Unknown error"
    }),500)

@app.route('/api/v1/users/<username>/comments', methods=["GET", "POST"])
def user_comments(username):
  if username.endswith("*"): username = username[:-1]
  if request.method == "GET":
    if request.args.get("page"):
      res = requests.get(f"https://scratch.mit.edu/site-api/comments/user/{username}?page={request.args.get('page')}")
    else:
      res = requests.get(f"https://scratch.mit.edu/site-api/comments/user/{username}")
    if res:
      try:
        res = html_to_json(res.text)["li"]
      except KeyError:
        return jsonify([])
      comments = []
      for comment in res:
        comments.append(render_comment_from_html(comment))
      return jsonify(comments)
    else:
      return make_response(jsonify({
        "error": "Unknown error"
      }),500)
  elif request.method == "POST":
    if request.args.get("comment") == None:
      return make_response(jsonify({
        "error": "No comment specified"
      }),400)
    try:
      token = request.headers["x-token"]
    except KeyError:
      auth = request.get_json()
      username = auth["username"]
      password = auth["password"]
      headers = {
        "x-CSRFToken": "a",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": "scratchcsrftoken=a;scratchlanguage=en;",
        "Referer": "https://scratch.mit.edu",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"
      }
      json = {
        "username": username,
        "password": password
      }
      res = requests.post("https://scratch.mit.edu/login", json=json, headers=headers)
      try:
        token = re.search("scratchcsrftoken=(.*?);", res.headers["Set-Cookie"]).group(1)
      except AttributeError:
        return jsonify({
          "error": "Incorrect username or password"
        })

    headers = {
      "Cookie": f"scratchcsfrtoken={token}",
      "Referer": "https://scratch.mit.edu/",
      "X-CSFRToken": token
    }
    json = {
      "content": request.args.get("comment"),
      "parent_id": "",
      "commetee_id": ""
    }
    res = requests.post(f"https://scratch.mit.edu/site-api/comments/user/{username}/add", json=json, headers=headers)
    if res:
      return make_response(jsonify({
        "success": "Comment added"
      }),201)
    else:
      return make_response(jsonify({
        "error": "Unknown error"
      }),500)

@app.route('/api/v1/users/<username>/comments/<id>', methods=["GET", "DELETE"])
def user_comments_id(username,id):
  if request.method == "GET":
    page = 1 if request.args.get("page") == None else int(request.args.get("page"))
    res = requests.get(f"https://scratch.mit.edu/site-api/comments/user/{username}?page={page}")
    try:
      res = html_to_json(res.text)["li"]
    except KeyError:
      return make_response(jsonify({"error":"User has no comments on thier page"}),404)
    comments = []
    for comment in res:
      comments.append(render_comment_from_html(comment))
    for comment in comments:
      if comment["id"] == id:
        return comment
    return make_response(jsonify({"error":"Couldn't find comment"}),404)
    

@app.route("/docs/<version>")
def docs(version):
  return render_template(f"docs/{version}.html")

app.run(host='0.0.0.0', port=8080)