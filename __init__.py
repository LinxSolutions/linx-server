from flask import Flask, render_template, url_for

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download')
def download():
    return render_template('download.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)