from flask import Flask, jsonify, url_for, make_response, request
import requests
app = Flask(__name__)

def normal_user_to_partial_user(user):
    return {
      "username": user["username"],
      "id": user["id"],
      "image_id": user["profile"]["id"]
    }
  

@app.route('/api/')
def api():
  return jsonify({
    "home": url_for("home")
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
  ocular_res = requests.get(f"https://my-ocular.jeffalo.net/api/user/{username}")
  if res and ocular_res:
    res = res.json()
    ocular_res = ocular_res.json()
    
    json = {
      "username": res["username"],
      "id": res["id"],
      "about": res["profile"]["bio"],
      "working_on": res["profile"]["status"],
      "status": ocular_res["status"],
      "status_colour": ocular_res["color"],
      "scratch_team": res["scratchteam"],
      "image_id": res["profile"]["id"],
      "country": res["profile"]["country"],
      "join_date": res["history"]["joined"][:10],
      "join_time": res["history"]["joined"][11:-5]
    }
    if request.args.get("nofollow") == None:
      json["following"] = following
      json["followers"] = followers

    return jsonify(json)
  elif res.status_code == 404:
    return make_response(jsonify({
      "error": "User does not exist"
    }),404)
  else:
    return make_response(jsonify({
      "error": "Unknown error"
    }),500)

app.run(host='0.0.0.0', port=8080)