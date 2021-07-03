import dns.update as dnsupdate
import dns.query as dnsquery
import dns.resolver as dnsresolver

USERNAME = "uurnikhost"
PASSWORD = "coOlAdmIn"
# username=uurnikhost&password=admin!2345@


from flask import Flask, request

app = Flask(__name__)


@app.route("/nic")
def hello_world():

    if request.args.get("username") == USERNAME:
        if request.args.get("password") == PASSWORD:

            try:
                hostname = request.args.get("hostname").split(".")[0]
                update = dnsupdate.Update("uurnikconnect.com")
                update.replace(hostname, 300, "A", request.args.get("myip"))
                _response = dnsquery.tcp(update, "dockerhost", timeout=5)
                return " ", 200
            except:
                return " ", 401

        else:
            return " ", 401
    else:
        return " ", 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
