from tracking_software import User, db, app

with app.app_context():
    user = User(username="admin")
    user.set_password("admin123")
    db.session.add(user)
    db.session.commit()
    print("✅ Admin user created successfully.")
