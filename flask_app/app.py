from website import create_app, db

app = create_app()

# ✅ Ensure database tables are created inside the app context
with app.app_context():
    db.create_all()  # ✅ This ensures tables exist before running Flask

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
