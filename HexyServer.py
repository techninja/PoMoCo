import string, cgi, time, json
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from HexyPresetController import BotPresetControl
bot = BotPresetControl()

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            op = self.path[1:]
            self.end_headers()
            self.wfile.write(json.dumps({'operation': op}))
            bot.parseTextCommand(op)
            return
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)


def main():
    try:
        server = HTTPServer(('', 80), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()
        bot.estop()

if __name__ == '__main__':
    main()

