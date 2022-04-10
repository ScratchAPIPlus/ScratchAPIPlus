from flask import Flask, jsonify, url_for, make_response, request, render_template, send_from_directory
import requests, os, re
from html_to_json import convert as html_to_json
import json as j

app = Flask(__name__)


def normal_user_to_partial_user(user):
    return {"username": user["username"], "id": user["id"]}


def render_comment_from_html(comment):
    try:
        comment["ul"][0]["li"]
    except KeyError:
        try:
            comment["div"][0]["div"][1]["div"][1]["_value"]
        except KeyError:
            return {
                "id": int(comment["div"][0]["_attributes"]["data-comment-id"]),
                "user": {
                    "username":
                    comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
                    "id":
                    comment["div"][0]["a"][0]["img"][0]["_attributes"]
                    ["src"].replace("//cdn2.scratch.mit.edu/get_image/user/",
                                    "").replace("_60x60.png", "")
                },
                "comment": "",
                "replies": []
            }
        else:
            return {
                "id": int(comment["div"][0]["_attributes"]["data-comment-id"]),
                "user": {
                    "username":
                    comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
                    "id":
                    comment["div"][0]["a"][0]["img"][0]["_attributes"]
                    ["src"].replace("//cdn2.scratch.mit.edu/get_image/user/",
                                    "").replace("_60x60.png", "")
                },
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
                    "id":
                    int(reply_comment["div"][0]["_attributes"]
                        ["data-comment-id"]),
                    "user": {
                        "username":
                        reply_comment["div"][0]["div"][1]["div"][0]["a"][0]
                        ["_value"],
                        "id":
                        reply_comment["div"][0]["a"][0]["img"][0]
                        ["_attributes"]["src"].replace(
                            "//cdn2.scratch.mit.edu/get_image/user/",
                            "").replace("_60x60.png", "")
                    },
                    "comment":
                    ""
                })
            else:
                replies.append({
                    "id":
                    int(reply_comment["div"][0]["_attributes"]
                        ["data-comment-id"]),
                    "user": {
                        "username":
                        reply_comment["div"][0]["div"][1]["div"][0]["a"][0]
                        ["_value"],
                        "id":
                        reply_comment["div"][0]["a"][0]["img"][0]
                        ["_attributes"]["src"].replace(
                            "//cdn2.scratch.mit.edu/get_image/user/",
                            "").replace("_60x60.png", "")
                    },
                    "comment":
                    reply_comment["div"][0]["div"][1]["div"][1]["_value"]
                })
        try:
            comment["div"][0]["div"][1]["div"][1]["_value"]
        except KeyError:
            return {
                "id": int(comment["div"][0]["_attributes"]["data-comment-id"]),
                "user": {
                    "username":
                    comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
                    "id":
                    comment["div"][0]["a"][0]["img"][0]["_attributes"]
                    ["src"].replace("//cdn2.scratch.mit.edu/get_image/user/",
                                    "").replace("_60x60.png", "")
                },
                "comment": "",
                "replies": replies
            }
        else:
            return {
                "id": int(comment["div"][0]["_attributes"]["data-comment-id"]),
                "user": {
                    "username":
                    comment["div"][0]["div"][1]["div"][0]["a"][0]["_value"],
                    "id":
                    comment["div"][0]["a"][0]["img"][0]["_attributes"]
                    ["src"].replace("//cdn2.scratch.mit.edu/get_image/user/",
                                    "").replace("_60x60.png", "")
                },
                "comment": comment["div"][0]["div"][1]["div"][1]["_value"],
                "replies": replies
            }


@app.route('/')
def home():
    r = make_response(render_template('home.html'), 200)
    return r


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route('/api/v1/')
def api():
    return jsonify({
        "home": url_for('home'),
        "docs": url_for('docs', version='v1')
    })


@app.route('/api/v1/home/')
def home_api():
    res = requests.get('https://api.scratch.mit.edu/proxy/featured').json()
    return jsonify({
        "featured_projects": [{
            "id": project["id"],
            "title": project["title"],
            "description": project["description"],
            "thumbnail": project["thumbnail"],
            "url": project["url"]
        } for project in res["community_featured_projects"]],
        "featured_studios": [{
            "id": studio["id"],
            "name": studio["name"],
            "thumbnail_utl": studio["thubnail_url"],
        } for studio in res["featured_studios"]]
    })


@app.route('/api/v1/users/<username>/')
def user(username):
    if len(username) > 20: return jsonify({"error": "username to long"})
    if len(username) > 3: return jsonify({"error": "username to short"})
    if username.endswith("*"): username = username[:-1]
    res = requests.get(f"https://api.scratch.mit.edu/users/{username}")
    if request.args.get("nofollow") == None:
        following_res = requests.get(
            f"https://api.scratch.mit.edu/users/{username}/following").json()
        followers_res = requests.get(
            f"https://api.scratch.mit.edu/users/{username}/followers").json()
        following = []
        followers = []
        for follow in following_res:
            following.append(normal_user_to_partial_user(follow))
        for follow in followers_res:
            followers.append(normal_user_to_partial_user(follow))
    if request.args.get("noprojects") == None:
        projects = []
        projects_res = requests.get(
            f"https://api.scratch.mit.edu/users/{username}/projects").json()
        for project in projects_res:
            projects.append({
                "id": project["id"],
                "instrutions": project["instructions"],
                "notes": project["description"],
                "title": project["title"],
                "public": project["public"],
                "comments_allowed": project["comments_allowed"],
                "stats": project["stats"]
            })
    if request.args.get("noactivity") == None:
        pass
    if request.args.get("nostatus") == None:
        ocular_res = requests.get(
            f"https://my-ocular.jeffalo.net/api/user/{username}")
    if res:
        res = res.json()
        json = {
            "username": res["username"],
            "id": res["id"],
            "about": res["profile"]["bio"],
            "working_on": res["profile"]["status"],
            "scratch_team": res["scratchteam"],
            "country": res["profile"]["country"],
            "join_date": res["history"]["joined"][:10],
            "join_time": res["history"]["joined"][11:-5]
        }
        if request.args.get("nofollow") == None:
            json["following"] = following
            json["followers"] = followers
        if request.args.get("noprojects") == None:
            json["projects"] = projects
        if request.args.get("nostatus") == None:
            ocular_res = ocular_res.json()
            try:
                json["status"] = ocular_res["status"]
                json["status_colour"] = ocular_res["color"]
            except KeyError:
                json["status"] = None
                json["status_colour"] = None

        return jsonify(json)
    elif res.status_code == 404:
        return make_response(jsonify({"error": "User does not exist"}), 404)
    else:
        return make_response(jsonify({"error": "Unknown error"}), 500)


@app.route('/api/v1/users/<username>/comments/', methods=["GET", "POST"])
def user_comments(username):
    if username.endswith("*"): username = username[:-1]
    if request.method == "GET":
        if request.args.get("page"):
            res = requests.get(
                f"https://scratch.mit.edu/site-api/comments/user/{username}?page={request.args.get('page')}"
            )
        else:
            res = requests.get(
                f"https://scratch.mit.edu/site-api/comments/user/{username}")
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
            return make_response(jsonify({"error": "Unknown error"}), 500)
    elif request.method == "POST":
        payload = request.get_json()
        try:
            token = request.headers["x-csfrtoken"]
        except KeyError:
            return make_response(
                jsonify({
                    "error":
                    "No token provided. You must specify a x-csfrtoken header."
                }), 401)

        headers = {
            "cookie":
            f"scratchcsrftoken={token};",
            "referer":
            "https://scratch.mit.edu/users/{username}/",
            "x-csrftoken":
            token,
            "x-requested-with":
            "XMLHttpRequest",
            "User-Agent":
            "Mozilla/5.0 (X11; CrOS x86_64 14588.23.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36"
        }
        json = {
            "content": payload["comment"],
            "parent_id": "",
            "commetee_id": ""
        }
        res = requests.post(
            f"https://scratch.mit.edu/site-api/comments/user/{username}/add",
            json=j.dumps(json),
            headers=headers)
        print(res.text)
        if res and res.json()["success"] == 0:
            return make_response(jsonify({"success": "Comment added"}), 201)
        else:
            return make_response(jsonify({"error": "Unknown error"}), 500)


@app.route('/api/v1/users/<username>/comments/<id>/',
           methods=["GET", "DELETE"])
def user_comments_id(username, id):
    if request.method == "GET":
        page = 1 if request.args.get("page") == None else int(
            request.args.get("page"))
        res = requests.get(
            f"https://scratch.mit.edu/site-api/comments/user/{username}?page={page}"
        )
        try:
            res = html_to_json(res.text)["li"]
        except KeyError:
            return make_response(
                jsonify({"error": "User has no comments on thier page"}), 404)
        comments = []
        for comment in res:
            comments.append(render_comment_from_html(comment))
        for comment in comments:
            if comment["id"] == id:
                return comment
        return make_response(jsonify({"error": "Couldn't find comment"}), 404)


@app.route('/api/v1/projects/<id>/comments/', methods=["GET", "POST"])
def project_comments(id):
    if request.method == "GET":
        if request.args.get("page"):
            res = requests.get(
                f"https://scratch.mit.edu/site-api/comments/project/{id}?page={request.args.get('page')}"
            )
        else:
            res = requests.get(
                f"https://scratch.mit.edu/site-api/comments/project/{id}")
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
            return make_response(jsonify({"error": "Unknown error"}), 500)


@app.route('/api/v1/projects/<id>/comments/<comment_id>/',
           methods=["GET", "DELETE"])
def project_comment_id(id, comment_id):
    if request.method == "GET":
        page = 1 if request.args.get("page") == None else int(
            request.args.get("page"))
        res = requests.get(
            f"https://scratch.mit.edu/site-api/comments/project/{id}?page={page}"
        )
        try:
            res = html_to_json(res.text)["li"]
        except KeyError:
            return make_response(
                jsonify({"error": "User has no comments on thier page"}), 404)
        comments = []
        for comment in res:
            comments.append(render_comment_from_html(comment))
        for comment in comments:
            if comment["id"] == int(comment_id):
                return comment
        return make_response(jsonify({"error": "Couldn't find comment"}), 404)


@app.route('/api/v1/search/<query>/')
def search(query):
    sort_by = "popular" if request.args.get(
        "sort_by") == None or request.args.get(
            "sort_by") == "popular" else "trending"
    res = requests.get(
        f"https://api.scratch.mit.edu/search/projects?limit=16&offset=0&language=en&mode={sort_by}&q={query}"
    )
    if res:
        res = res.json()
        projects = []
        for project in res:
            projects.append({
                "author":
                normal_user_to_partial_user(project["author"]),
                "id":
                project["id"],
                "instrutions":
                project["instructions"],
                "notes":
                project["description"],
                "title":
                project["title"],
                "public":
                project["public"],
                "comments_allowed":
                project["comments_allowed"],
                "stats":
                project["stats"]
            })
        return jsonify(projects)
    else:
        return jsonify({"error": "Unknown error occred"}, 500)


@app.route("/docs/<version>/")
def docs(version):
    return render_template(f"docs/{version}.html")


app.run(host='0.0.0.0', port=8080)
