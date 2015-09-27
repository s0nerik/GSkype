#!/usr/bin/python
from gi.repository import Gtk, WebKit2, Notify
import json
import traceback

# saved_username = "olex95"
# saved_password = "q1w2e3r4t5"

saved_username = "thesonerik@gmail.com"
saved_password = "q1w2e3r4t5"


class Application:
    def __init__(self):
        self.icon = Gtk.Image.new_from_file("skype_icon.png").get_pixbuf()

        self.builder = self.create_builder()

        self.win = self.builder.get_object("applicationwindow")
        self.win.connect("delete-event", self.stop)
        self.win.set_size_request(1024, 768)

        self.scroll_view = self.builder.get_object("scrolledwindow")

        self.web_view = WebKit2.WebView()
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
        self.web_view.connect("submit-form", self._on_form_submit)
        self.web_view.load_uri("https://web.skype.com/en/")
        self.web_view.connect("load-finished", self.autofill)

    def autofill(self, web_view, frame):
        uri = str(web_view.get_uri())
        if uri.find("login.skype.com") == -1 and uri.find("login.live.com") == -1:
            return

        if not saved_username or not saved_password:
            return

        doc = web_view.get_dom_document()

        username = doc.get_element_by_id("username")
        password = doc.get_element_by_id("password")
        btn_sign_in = doc.get_element_by_id("signIn")

        if not username:
            username = doc.get_element_by_id("i0116")

        if not password:
            password = doc.get_element_by_id("i0118")

        if not btn_sign_in:
            btn_sign_in = doc.get_element_by_id("idSIButton9")

        try:
            username.set_value(saved_username)
            password.set_value(saved_password)

            btn_sign_in.click()
        except:
            print("Can't autofill credentials")
            print(traceback.format_exc())

    def _on_form_submit(self, web_view, request):
        fields = request.get_text_fields()
        print(fields)

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