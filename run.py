from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False, port=5002, use_reloader=False ) 