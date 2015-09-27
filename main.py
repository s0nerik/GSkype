#!/usr/bin/python
from gi.repository import Gtk, WebKit, Notify
import json
import traceback


class Application:
    def __init__(self):
        self.saved_username = "thesonerik@gmail.com"
        self.saved_password = "q1w2e3r4t5"
        # self.saved_password = None

        self.input_username = ""
        self.input_password = ""

        self.logged_in = False

        self.icon = Gtk.Image.new_from_file("skype_icon.png").get_pixbuf()

        self.builder = self.create_builder()

        self.win = self.builder.get_object("applicationwindow")
        self.win.connect("delete-event", self.stop)
        self.win.set_size_request(512, 512)

        self.scroll_view = self.builder.get_object("scrolledwindow")

        self.web_view = WebKit.WebView()
        self.scroll_view.add(self.web_view)

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

    def _make_window_bigger(self):
        self.win.set_size_request(1024, 768)

    def _on_user_changed_contents(self, web_view):
        print("user_changed_contents")
        username, password, btn_sign_in = self._get_login_form_parts(web_view)
        self.input_username = username.get_value()
        self.input_password = password.get_value()

    def _save_autofill_data(self):
        self.saved_username = self.input_username
        self.saved_password = self.input_password

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
                self._save_autofill_data()
                self.logged_in = True

            if self.logged_in:
                self._make_window_bigger()

    def _autofill_data(self, web_view):
        if not self.saved_username or not self.saved_password:
            return

        username, password, btn_sign_in = self._get_login_form_parts(web_view)

        try:
            username.set_value(self.saved_username)
            password.set_value(self.saved_password)

            btn_sign_in.click()

            self.logged_in = True
        except:
            print("Can't autofill credentials")
            print(traceback.format_exc())

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

                # print(response_json)

    def notify_new_message(self, author, message, time):
        notification = Notify.Notification.new(author, message, None)
        notification.add_action("1337", "", self.show)
        notification.set_image_from_pixbuf(self.icon)
        notification.show()

    def set_notification(self, enabled):
        status_icon = Gtk.StatusIcon.new_from_icon_name("emblem-important")
        status_icon.set_visible(enabled)

    @staticmethod
    def create_builder():
        builder = Gtk.Builder()
        builder.add_from_file("layout.glade")
        return builder


app = Application()
app.start()
app.load_skype_url()
app.set_notification(True)

Gtk.main()