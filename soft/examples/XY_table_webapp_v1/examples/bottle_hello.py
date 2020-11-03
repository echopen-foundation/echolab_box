from bottle import route, run, template

@route('/hello/<name>')
def index(name):
    return template('<b>Hello2 {{name}}</b>!', name=name)

run(host='0.0.0.0', port=8080, reloader=True)
