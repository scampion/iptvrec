import datetime
import os

import m3u8
import subprocess
from flask import Flask, render_template_string, request

recdic = "/media/diskA"

loopwget = """#!/bin/bash
while true; do
 wget $1 -O ->> $2;
done
"""

with open('/usr/local/bin/loopwget', 'w') as b:
    b.write(loopwget)

html = """
<html>
<body>
<script>
    function removeSpaces(string) {
     return string.split(' ').join('');
    }
</script>
<form action="search">
  <input type="text" name="query" >
  <input type="submit" value="Search">
</form>
<hr>
  {% for k, stream in data %}
    <form action="record">
        <input type="text" readonly="readonly" name="channel" value={{k | replace(' ','_') }} size=40 >
        <input type="hidden" name="stream" value="{{stream}}">
        <input type="text" name="start" value="21:00" size="6" onkeyup="this.value=removeSpaces(this.value);">
        <input type="text" name="stop" value="23:00" size="6" onkeyup="this.value=removeSpaces(this.value);">
        {% for h, d in dates %}
            <input type="radio" name="days" value="{{d}}" {% if loop.index == 1 %}checked{% endif %}> {{h}}
        {% endfor %}
        <input type="text" name="title" value="name" onkeyup="this.value=removeSpaces(this.value);" size="30">
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
    for j, date in [l.split('\t') for l in subprocess.getoutput("atq").split('\n') if l]:
        yield "%s %s" % (date, subprocess.getoutput("at -c %s" % j).split('\n')[-2])


def get_duration(start, stop):
    h, m = start.split(':')
    b = datetime.datetime.now()
    b = b.replace(hour=int(h), minute=int(m))

    h, m = stop.split(':')
    e = datetime.datetime.now()
    if int(h) <= 5:
        e += datetime.timedelta(days=1)
    e = e.replace(hour=int(h), minute=int(m))
    return int((e - b).total_seconds())

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
    results = list(find(searchword))
    dates = [(datetime.datetime.now() + datetime.timedelta(days=d)) for d in range(10)]
    dates = [(d.strftime('%a %d'), d.strftime('%m/%d/%Y')) for d in dates]
    return render_template_string(html, data=results, dates=dates)


@app.route('/record')
def record():
    global recdic
    with open("/tmp/record", 'w') as r:
        ofile = os.path.join(recdic, request.args['title'] + ".ts")
        duration = get_duration(request.args['start'], request.args['stop'])
        args = (duration, request.args['stream'], ofile, request.args['start'], request.args['days'])
        r.write("echo 'timeout %s loopwget %s %s' | at %s %s\n" % args)
        r.write("echo 'sleep %s && ffmpeg -i %s -codec:v copy -codec:a copy %s && rm %s' | at %s %s\n" %
                (duration, ofile, ofile.replace(".ts", ".mp4"), ofile, request.args['start'], request.args['days']))
    subprocess.check_output(['sh', '/tmp/record'])
    return "done"


if __name__ == '__main__':
    app.run(host='0.0.0.0')
