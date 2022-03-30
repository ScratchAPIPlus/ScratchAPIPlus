from flask import Flask, jsonify, url_for, make_response, request, render_template, send_from_directory
import requests, os
from html_to_json import convert as html_to_json
app = Flask(__name__)

def normal_user_to_partial_user(user):
    return {
      "username": user["username"],
      "id": user["id"],
      "image_id": user["profile"]["id"]
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
    "home": url_for("home"),
    "docs": url_for("static", filename="docs/v1/index.html")
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
  # https://scratch.mit.edu/site-api/comments/user/OS_Cool_/
  # https://scratch.mit.edu/site-api/comments/user/OS_Cool_/add/
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
        try:
          comment["ul"][0]["li"]
        except KeyError:
          try:
            comment["div"][0]["div"][1]["div"][1]["_value"]
          except KeyError:
            comments.append({
              "id": int(comment["div"][0]["_attributes"]["data-comment-id"]),
              "username": comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
              "comment": "",
              "replies": []
            })
          else:
            comments.append({
              "id": int(comment["div"][0]["_attributes"]["data-comment-id"]),
              "username": comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
              "comment": comment["div"][0]["div"][1]["div"][1]["_value"],
              "replies": []
            })
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
            comments.append({
              "id": int(comment["div"][0]["_attributes"]["data-comment-id"]),
              "username": comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
              "comment": "",
              "replies": replies
            })
          else:
            comments.append({
              "id": int(comment["div"][0]["_attributes"]["data-comment-id"]),
              "username": comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
              "comment": comment["div"][0]["div"][1]["div"][1]["_value"],
              "replies": replies
            })
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
    token = request.headers["x-token"]
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

app.run(host='0.0.0.0', port=8080)