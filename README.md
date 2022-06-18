# Sensor Tracking for SmartThings

[![license](https://img.shields.io/github/license/pronovic/sensor-track)](https://github.com/pronovic/sensor-track/blob/master/LICENSE)
[![Test Suite](https://github.com/pronovic/sensor-track/workflows/Test%20Suite/badge.svg)](https://github.com/pronovic/sensor-track/actions?query=workflow%3A%22Test+Suite%22)
[![coverage](https://coveralls.io/repos/github/pronovic/sensor-track/badge.svg?branch=master)](https://coveralls.io/github/pronovic/sensor-track?branch=master)
[![release](https://img.shields.io/github/v/release/pronovic/sensor-track)](https://github.com/pronovic/sensor-track/releases/latest)

This is a SmartApp that is used to historically track data from SmartThings
temperature and humidity sensors. Optionally, users with U.S.-based locations
can choose to periodically capture current temperature and humidity, sourced
from the National Weather Service API.

The SmartApp is written in Python 3 using the [smartapp-sdk](https://pypi.org/project/smartapp-sdk/) package.  It 
is designed to run as a systemd user service writing data 
to [InfluxDB 2](https://docs.influxdata.com/influxdb/v2.2/) for later visualization with a
tool such as [Grafana](https://grafana.com/).

## Cautions & Limitations

**_This is a developer-focused tool._**

My goal was to write something I could use myself on my own hardware, looking
forward toward a possible later transition to AWS Lambda.  The code is well
tested and functions properly, but I haven't spent a lot of effort on making
the installation process simple.  If you're not already comfortable with the
UNIX command line, you may have a hard time getting this to work. 

**_Only one user can install the resulting SmartApp._**

When following the instructions below, only the user that registers the
SmartApp in the Developer Console will be able to use it.  Supporting broader
access to more users requires formal enrollment with SmartThings, and that
process is outside the scope of this document.

## Developer Documentation

Developer documentation is found in [DEVELOPER.md](DEVELOPER.md).  See that
file for notes about how the code is structured, how to set up a development
environment, etc.

## Installing Prerequisites

The SmartApp needs to write to an [InfluxDB 2](https://docs.influxdata.com/influxdb/v2.2/) 
database server.  You probably also want to install a data visualization tool that works
with InfluxDB, such as [Grafana](https://grafana.com/), although that is outside the
scope of this documentation.

Install InfluxDB using the instructions on 
the [InfluxDB downloads page](https://portal.influxdata.com/downloads/).  On a Debian
server, it's easiest to set up an apt source and install the Debian packages:

```
$ apt-get install influxdb2
```

When you're done, run the setup process:

```
$ sudo influx setup
> Welcome to InfluxDB 2.0!
? Please type your primary username influx
? Please type your password **************** 
? Please type your password again ****************
? Please type your primary organization name iot
? Please type your primary bucket name metrics
? Please type your retention period in hours, or 0 for infinite 0
? Setup with these parameters?
  Username:          influx
  Organization:      iot
  Bucket:            metrics
  Retention Period:  infinite
 Yes
User  Organization   Bucket
influx   iot      metrics
```

Then create a user to associate with your SmartApp:

```
$ sudo influx user create -n sensortrack -p somepassword -o iot
ID       Name
09875e2210877000  sensortrack
```

Finally, create an authorization token that the sensortrack service can use for
the InfluxDB API:

```
$ sudo influx auth create -u sensortrack -o iot --write-buckets
ID       Description Token                                  User Name   User ID        Permissions

09873344ad1b7000        BicWm9vn1Z0Th_o4fDkKWM2Ze6sTVAuKHnhov77XRdlmbkPPPPsssavvv3AH7UIKCg10d0RTB1lC8ipWXFtnjw==  sensortrack 09875e2210877000  [write:orgs/e7d4effddda1046f/buckets]
```

Make sure you save off all of the information you need for the later setup
steps.  You will need to know the URL and port (`:8086`) of the server, the
organization (`iot`), the default bucket (`metrics`) and the token
(`BicWm...`).

## Installing the SmartApp Server

The platform is distributed at GitHub.  To install the software, download the `.whl`
file for the [latest release](https://github.com/pronovic/sensor-track/releases/latest),
and install it using `pip`, like:

```
$ pip install sensor_track-0.1.0-py3-none-any.whl
```

Next, configure the platform.  Download the configuration bundle for the latest
release.  Extract the tar file to your user configuration directory:

```
$ mkdir -p ~/.config
$ tar zxvf sensor_track-config-0.1.0.tar.gz -C ~/.config
```

This creates two directories within `~/.config`.  The `systemd` directory
contains configuration for the systemd user service that you will create
shortly:

```
systemd/user/sensortrack.service
```

The webserver server runs on port 8080 by default.  If you want it to run on a
different port, edit `sensortrack.service` and make the appropriate adjustment.

By default, the webserver accepts connections on all interfaces (0.0.0.0).  Depending
on your infrastructure, you may be able to restrict this to 127.0.0.1 instead.  If
you want to do this, edit `sensortrack.service` and make the appropriate adjustment.

The `sensortrack` directory contains configuration for the sensortrack daemon process.

```
sensortrack/server/application.yaml
sensortrack/server/logging.yaml
sensortrack/server/server.env
```

Edit `server.env` and configure the connection to InfluxDB, using the values
you saved off above.

Next, configure systemd:

```
$ sudo loginctl enable-linger <your-user>    # restart user services at reboot
$ systemctl --user enable sensortrack        # enable the sensortrack service
$ systemctl --user start sensortrack         # start the sensortrack service
$ systemctl --user status sensortrack        # show status for the sensortrack service
```

At this point, the systemd service should be running.  Check that it is
listening:

```
$ curl -X GET http://localhost:8080/health
$ curl -X GET http://localhost:8080/version
```

You can also check the logs from the service:

```
$ journalctl --pager-end --user-unit sensortrack
```

If you do need to change any of the systemd config files, make sure
to reload them afterwards, before trying to do any further testing:

```
$ systemctl --user daemon-reload
```

Finally, reboot and confirm that the service starts automatically.  After
reboot, use the same curl commands or check the logs to confirm everything is
ok.

## Expose Your Endpoint

Any SmartApp must have an endpoint that is available on the public internet
over HTTPS.  The exact mechanism to accomplish this depends on what your
infrastructure looks like.  I already run an Apache webserver that supports
HTTPS, so I used [this article](https://www.digitalocean.com/community/tutorials/how-to-use-apache-as-a-reverse-proxy-with-mod_proxy-on-debian-8) as 
a starting point, and configured apache to proxy public requests to my
sensortrack service.

First, I enabled some modules:

```
$ a2enmod proxy
$ a2enmod proxy_http
$ a2enmod proxy_balancer
$ a2enmod lbmethod_byrequests
```

Then, I added the following block to my existing Apache configuration:

```
# Sensor Tracking SmartApp
ProxyPreserveHost On
ProxyPass         "/smartthings/myapp" "http://192.168.1.120:8080"
ProxyPassReverse  "/smartthings/myapp" "http://192.168.1.120:8080"
```

With this configuration in place, your SmartApp will be located at:

```
https://<yourhost>/smartthings/myapp/smartapp
```

The same `/health` and `/version` endpoints you tested above will also be
exposed, although SmartThings doesn't need to know about them.  Spot-check that
the external URL appears to be working.

## Register Your SmartApp with SmartThings

Now that you have a working webserver and you can look at the logs, you have
everything you need to actually create and install the SmartApp in the
SmartThings infrastructure.

First, make sure that you have a console window open.  Watch the SmartApp logs
with `journalctl`, as described above.

Next, log into the [Developer Workspace](https://smartthings.developer.samsung.com/workspace/) with 
your Samsung Account credentials.  Once there:

- Click **New Project**
- Click **Continue** under **Automation for the SmartThings App**
- Enter a project name and click **Create Project**
- In the next screen, click **Register App**
- Choose the **Webhook Endpoint** option
- Paste in the URL for your webhook

At this point, the SmartThings infrastructure will send a `CONFIRMATION` event
to your webhook.  The application will handle that event and log an application
ID and a confirmation URL that you can see using `journalctl`.  Copy out that
URL and view it in a browser.  This step confirms that you control the webhook.

Once you've done the initial connection here and the webhook has been
recognized, you have to mark your app as **Deployed to test**, and then you'll
be able to try installing it.

## Install the SmartApp

Samsung makes it difficult to install non-standard SmartApps. See this [community thread](https://community.smartthings.com/t/faq-did-we-lose-the-ability-to-add-custom-smartapps-after-the-app-update-of-june-2021/227734) for 
a discussion.  The process described below worked for me in June of 2022.

> _Note:_ If you haven't logged into the Developer Workspace at least once, this
> won't work.  But if you followed the instructions above, that should already
> be taken care of.

Follow the instructions to [Enable Developer Mode in the SmartThings App](https://developer-preview.smartthings.com/docs/devices/test-your-device/#enable-developer-mode-in-the-smartthings-app):

- Tap the **Menu** tab on the bottom navigation bar
- Tap the **Settings gear** icon 
- The SmartThings settings menu will appear
- Long-press **About SmartThings** for 5 seconds.
- A developer mode toggle will appear in the settings menu immediately below where you were long-pressing (it might not be obvious)
- Click the toggle to enable **Developer Mode**.
- You will be prompted to restart the SmartThings app

Once you've enabled Developer Mode and restarted, you need to find your
SmartApp:

- Tap on the **Automations** tab
- Click on **+** in the upper right of the screen
- Tap **Add Routine** and choose the **Discover** tab at the top
- Scroll all of the way to the bottom to find your custom SmartApp, which should have whatever name you registered above

This will immediately trigger a series of webhook `POST` requests to your
webserver.  If everything goes well, you will be prompted to configure the
SmartApp, and you will get the option to choose which devices to collect data
from.  If something goes wrong, you will get an error dialog in the app, and
you'll have to look in the `journalctl` logs to debug it.  If necessary, you
can adjust config files in `~/.config/sensortrack/server` to increase the log
level or enable JSON logging (but note that JSON logging exposes secrets into
your log).

Once you are done configuring the SmartApp, it will subscribe to events from
your sensors.  As those events flow into the webhook, they will be recorded in
InfluxDB.  There's no way to know exactly when the first event will be
triggered, so keep an eye on the logs and confirm that you don't see any
errors. You should see at least one event within the first hour or so,
depending on how you have your sensors configured.
