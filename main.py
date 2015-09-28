#!/usr/bin/python
from gi.repository import Gtk, WebKit, Notify
import json
import traceback
from pickle import Pickler, Unpickler
import os
import sys
from os.path import expanduser

home = expanduser("~")
gskype_settings_file = os.path.join(home, ".gskype", "settings")
gskype_state_file = os.path.join(home, ".gskype", "state")


class Application:
    def __init__(self):
        self._restore_settings()
        self._restore_state()

        if self.state['logged_out']:
            self.state['logged_out'] = False
            self._save_state()

        self.input_username = ""
        self.input_password = ""

        self.logged_in = False

        self.icon = Gtk.Image.new_from_file("skype_icon.png").get_pixbuf()

        self.builder = self.create_builder()

        self.win = self.builder.get_object("applicationwindow")
        self._make_window_smaller()

        self.scroll_view = self.builder.get_object("scrolledwindow")

        self.web_view = WebKit.WebView()
        self.scroll_view.add(self.web_view)

        self._connect_signals()

    def _connect_signals(self):
        self.win.connect("delete-event", self.stop)
        self.builder.get_object("switch_autologin").connect("toggled", self._on_autologin_toggled)
        self.builder.get_object("btn_logout").connect("activate", self._on_logout_clicked)

    def show(self):
        self.win.present()

    def start(self):
        Notify.init("GSkype")
        self.win.show_all()

    def stop(self):
        Notify.uninit("GSkype")
        Gtk.main_quit()

    def load_skype_url(self):
        self.web_view.connect("resource-load-finished", self._on_resource_load_finished)
        self.web_view.connect("load-finished", self._on_page_load_finished)
        self.web_view.connect("user-changed-contents", self._on_user_changed_contents)
        self.web_view.load_uri("https://web.skype.com/en/")

    def _make_window_smaller(self):
        self.win.set_size_request(512, 512)

    def _make_window_bigger(self):
        self.win.set_size_request(1024, 768)

    def _restore_settings(self):
        try:
            with open(gskype_settings_file, "rb") as f:
                self.settings = Unpickler(f).load()
        except:
            self.settings = {'autologin': True, 'username': '', 'password': ''}

    def _restore_state(self):
        try:
            with open(gskype_state_file, "rb") as f:
                self.state = Unpickler(f).load()
        except:
            self.state = {'logged_out': False}

    def _save_settings(self):
        os.makedirs(os.path.dirname(gskype_settings_file), exist_ok=True)
        with open(gskype_settings_file, "wb+") as f:
            Pickler(f).dump(self.settings)

    def _save_state(self):
        os.makedirs(os.path.dirname(gskype_state_file), exist_ok=True)
        with open(gskype_state_file, "wb+") as f:
            Pickler(f).dump(self.state)

    def _on_logout_clicked(self, btn):
        self.state['logged_out'] = True
        self._save_state()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _on_autologin_toggled(self, toggle):
        self.settings['autologin'] = toggle.get_active()
        self._save_settings()

    def _on_user_changed_contents(self, web_view):
        username, password, btn_sign_in = self._get_login_form_parts(web_view)
        self.input_username = username.get_value()
        self.input_password = password.get_value()

    def _save_autofill_data(self):
        self.settings['username'] = self.input_username
        self.settings['password'] = self.input_password
        self._save_settings()

    def _get_login_form_parts(self, web_view):
        doc = web_view.get_dom_document()

        username = doc.get_element_by_id("username")
        if not username:
            username = doc.get_element_by_id("i0116")

        password = doc.get_element_by_id("password")
        if not password:
            password = doc.get_element_by_id("i0118")

        btn_sign_in = doc.get_element_by_id("signIn")
        if not btn_sign_in:
            btn_sign_in = doc.get_element_by_id("idSIButton9")

        return username, password, btn_sign_in

    def _on_page_load_finished(self, web_view, frame):
        uri = str(web_view.get_uri())
        if "login.skype.com" in uri or "login.live.com" in uri:
            self._autofill_data(web_view)
        if uri.startswith("https://web.skype.com"):
            if self.input_username and self.input_password:
                self.logged_in = True
                self.state['logged_out'] = False
                self._save_autofill_data()
                self._save_state()

            if self.logged_in:
                self._make_window_bigger()

    def _autofill_data(self, web_view):
        if self.logged_in:
            return

        if not self.settings or not self.settings['username'] or not self.settings['password']:
            return

        username, password, btn_sign_in = self._get_login_form_parts(web_view)

        try:
            username.set_value(self.settings['username'])
            password.set_value(self.settings['password'])

            if not self.state['logged_out']:
                btn_sign_in.click()
                self.logged_in = True
            else:
                password.focus()
        except:
            pass
            # print("Can't autofill credentials")
            # print(traceback.format_exc())

    def _on_resource_load_finished(self, web_view, web_frame, web_resource):
        uri = str(web_resource.get_uri())
        if uri.endswith("poll"):
            response_json = web_resource.get_data().str
            parsed_response = json.loads(response_json)
            if parsed_response:
                msg = parsed_response["eventMessages"][0]
                if msg["resourceType"] == "NewMessage":
                    res = msg["resource"]
                    if res["messagetype"] == "Text":
                        self.notify_new_message(res["imdisplayname"], res["content"], res["originalarrivaltime"])

                print(response_json)

    def notify_new_message(self, author, message, time):
        notification = Notify.Notification.new(author, message, None)
        notification.add_action("1337", "", self.show)
        notification.set_image_from_pixbuf(self.icon)
        notification.show()

    @staticmethod
    def create_builder():
        builder = Gtk.Builder()
        builder.add_from_file("layout.glade")
        return builder


app = Application()
app.start()
app.load_skype_url()

Gtk.main()