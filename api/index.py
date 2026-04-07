from app import app

# Vercel Python runtime uses the WSGI app object named "app".
# This file routes all requests from vercel.json to the Flask app.

if __name__ == '__main__':
    app.run(debug=False, port=5000)
