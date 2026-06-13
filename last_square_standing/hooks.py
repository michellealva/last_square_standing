app_name = "last_square_standing"
app_title = "Last Square Standing"
app_publisher = "Michelle"
app_description = "A multiplayer elimination grid game"
app_email = "michelle@frappe.io"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "last_square_standing",
# 		"logo": "/assets/last_square_standing/logo.png",
# 		"title": "Last Square Standing",
# 		"route": "/last_square_standing",
# 		"has_permission": "last_square_standing.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/last_square_standing/css/last_square_standing.css"
# app_include_js = "/assets/last_square_standing/js/last_square_standing.js"

# include js, css files in header of web template
# web_include_css = "/assets/last_square_standing/css/last_square_standing.css"
# web_include_js = "/assets/last_square_standing/js/last_square_standing.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "last_square_standing/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "last_square_standing/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "last_square_standing.utils.jinja_methods",
# 	"filters": "last_square_standing.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "last_square_standing.install.before_install"
# after_install = "last_square_standing.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "last_square_standing.uninstall.before_uninstall"
# after_uninstall = "last_square_standing.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "last_square_standing.utils.before_app_install"
# after_app_install = "last_square_standing.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "last_square_standing.utils.before_app_uninstall"
# after_app_uninstall = "last_square_standing.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "last_square_standing.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "last_square_standing.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"last_square_standing.tasks.all"
# 	],
# 	"daily": [
# 		"last_square_standing.tasks.daily"
# 	],
# 	"hourly": [
# 		"last_square_standing.tasks.hourly"
# 	],
# 	"weekly": [
# 		"last_square_standing.tasks.weekly"
# 	],
# 	"monthly": [
# 		"last_square_standing.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "last_square_standing.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "last_square_standing.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "last_square_standing.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "last_square_standing.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["last_square_standing.utils.before_request"]
# after_request = ["last_square_standing.utils.after_request"]

# Job Events
# ----------
# before_job = ["last_square_standing.utils.before_job"]
# after_job = ["last_square_standing.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"last_square_standing.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

# Require all whitelisted methods to have type annotations
require_type_annotated_api_methods = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

