import datetime
import os

import m3u8
import subprocess
from flask import Flask, render_template_string, request

recdic = "/media/diskA"

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
        <input type="text" name="start" value="21:00" size="6">
        <input type="text" name="stop" value="23:00" size="6">
        {% for h, d in dates %}
            <input type="radio" name="days" value="{{d}}" {% if loop.index == 1 %}checked{% endif %}> {{h}}
        {% endfor %}
        <input type="text" name="title" value="name" size="30">
        <input type="submit" value="record">
    </form>
    <hr>
  {% endfor %}
<hr>
  <b>Record scheduled :</b> <br>
  {% for job in jobs %}
  {{job}}<br>
  {% endfor %}
</body>
</html>
"""


def jobs():
    for j in [l.split('\t')[0] for l in subprocess.getoutput("atq").split('\n')]:
        yield subprocess.getoutput("at -c %s" % j).split('\n')[-2]


app = Flask(__name__)


@app.route('/')
def hello():
    return render_template_string(html, jobs=list(jobs()))


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
    dates = [(datetime.datetime.now() + datetime.timedelta(days=d)) for d in range(10)]
    dates = [(d.strftime('%a %d'), d.strftime('%m/%d/%Y')) for d in dates]
    return render_template_string(html, data=results, dates=dates)


@app.route('/record')
def record():
    with open("/tmp/record", 'w') as r:
        args = [request.args.get(a, '') for a in ['stop', 'stream', 'title', 'start', 'days']]
        b = datetime.datetime.now()
        h, m = args[3].split(':')
        b = b.replace(hour=int(h), minute=int(m))
        e = datetime.datetime.now()
        h, m = args[0].split(':')
        e = e.replace(hour=int(h), minute=int(m))
        args[0] = str(int((e - b).total_seconds()))
        args = tuple([a.strip(' ') for a in args])
        print(args)
        r.write("echo 'timeout %s loopwget %s %s' | at %s %s" % args)
    subprocess.check_output(['sh', '/tmp/record'])
    return "done"


if __name__ == '__main__':
    app.run(host='0.0.0.0')
