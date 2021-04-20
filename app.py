import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_ideas")
def get_ideas():
    ideas = list(mongo.db.ideas.find())
    return render_template("ideas.html", ideas=ideas)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    ideas = list(mongo.db.ideas.find({"$text": {"$search": query}}))
    return render_template("ideas.html", ideas=ideas)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        #check the username
        existing_user = mongo.db.user.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists !")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        #put the new user into "session"cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful !")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("signin"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("signin"))

    return render_template("signin.html")

@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    #grab the session username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    if session["user"]:
        return render_template("profile.html", username=username)
    return redirect(url_for("signin"))


@app.route("/signout")
def signout():
    #remove user from session cookies
    flash("You have been Signed Out !")
    session.pop("user")
    return redirect(url_for("signin"))


@app.route("/add_idea", methods=["GET", "POST"])
def add_idea():
    if request.method == "POST":
        idea = {
            "category_name": request.form.get("category_name"),
            "idea_name": request.form.get("idea_name"),
            "idea_description": request.form.get("idea_description"),
            "idea_date": request.form.get("idea_date"),
            "created_by": session["user"]
        }
        mongo.db.ideas.insert_one(idea)
        flash("Idea Successfully Added")
        return redirect(url_for("get_ideas"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_idea.html", categories=categories)



@app.route("/edit_idea/<idea_id>", methods=["GET", "POST"])
def edit_idea(idea_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
            "idea_name": request.form.get("idea_name"),
            "idea_description": request.form.get("idea_description"),
            "idea_date": request.form.get("idea_date"),
            "created_by": session["user"]
        }
        mongo.db.ideas.update({"_id": ObjectId(idea_id)}, submit)
        flash("Idea Successfully Updated")

    idea = mongo.db.ideas.find_one({"_id": ObjectId(idea_id)})

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_idea.html", idea=idea, categories=categories)



@app.route("/delete_idea/<idea_id>")
def delete_idea(idea_id):
    mongo.db.ideas.remove({"_id": ObjectId(idea_id)}, 'submit')
    flash("Idea Successfully Removed")
    return redirect(url_for("get_ideas"))



@app.route("/rate_idea/<idea_id>")
def rate_idea(idea_id):
    mongo.db.ideas.find_one({"_id": ObjectId(idea_id)}, 'submit')
    flash("Thank You !")
    return redirect(url_for("get_ideas"))



@app.route("/get_categories")
def get_categories():
    categories = list(mongo.db.categories.find().sort('category_name', 1))
    return render_template("categories.html", categories=categories)



@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = {"category_name": request.form.get("category_name")}
        mongo.db.categories.insert_one(category)
        flash("Category Successfully Added")
        return redirect(url_for("get_categories"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_category.html", categories=categories)



@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
        }
        mongo.db.categories.update({"_id": ObjectId(idea_id)}, 'submit')
        flash("Category Successfully Updated")

    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template('edit_category.html', categories=categories)



@app.route("/delete_category/<category_id>") 
def delete_category(category_id):
    mongo.db.categories.remove({"_id": ObjectId(category_id)}, 'submit')
    flash("Category Successfully Removed")
    return redirect(url_for("get_categories"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
