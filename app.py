import os

import m3u8
import subprocess
from flask import Flask, render_template_string, request


recdic = "/media/diskA/"


loopwget = """#!/bin/bash
while true; do
 wget $1 -O ->> %s/$2.ts;
done
""" % recdic

with open('/usr/local/bin/loopwget', 'w') as b:
    b.write(loopwget)


html = """
<html>
<body>
<form action="search">
  <input type="text" name="query" >
  <input type="submit" value="Search">
</form>
<hr>
  {% for k, stream in data %}
    <form action="record">
        <input type="text" readonly="readonly" name="channel" value={{k | replace(' ','_') }} size=40 >
        <input type="hidden" name="stream" value="{{stream}}">
        <input type="text" name="time" value="21:00" size="6">
        <input type="text" name="title" value="name" size="30">
        <input type="text" name="duration" value="9000" size="5">
        <input type="submit" value="record">
    </form>
    <hr>
  {% endfor %}
</body>
</html>
"""

app = Flask(__name__)


@app.route('/')
def hello():
    return render_template_string(html)


@app.route('/search')
def search():
    def find(str):
        for f in os.listdir("."):
            if f.endswith('m3u'):
                for s in m3u8.loads(open(f, encoding='utf8').read()).segments:
                    if str in s.title.lower() and s.title.startswith('FR'):
                        yield s.title, s.uri

    searchword = request.args.get('query', '')
    print(searchword)
    results = list(find(searchword))
    return render_template_string(html, data=results)


@app.route('/record')
def record():
    with open("/tmp/record", 'w') as r:
        args = [request.args.get(a, '') for a in ['duration', 'stream', 'title', 'time']]
        args = tuple([a.strip(' ') for a in args])
        r.write("echo 'timeout %s loopwget %s %s' | at %s" % args)
    subprocess.check_output(['sh', '/tmp/record'])
    return "done"

if __name__ == '__main__':
    app.run(host='0.0.0.0')
