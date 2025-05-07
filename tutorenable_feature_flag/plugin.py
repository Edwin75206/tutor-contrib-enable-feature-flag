from __future__ import annotations

import os
import os.path
from glob import glob

import click
import pkg_resources
from tutor import hooks

from .__about__ import __version__

########################################
# CONFIGURATION
########################################

hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        # Add your new settings that have default values here.
        # Each new setting is a pair: (setting_name, default_value).
        # Prefix your setting names with 'ENABLE_FEATURE_FLAG_'.
        ("ENABLE_FEATURE_FLAG_VERSION", __version__),
        ("STUDIO_REQUEST_EMAIL", "admin@example.com"),
    ]
)

hooks.Filters.CONFIG_UNIQUE.add_items(
    [
        # Add settings that don't have a reasonable default for all users here.
        # For instance: passwords, secret keys, etc.
        # Each new setting is a pair: (setting_name, unique_generated_value).
        # Prefix your setting names with 'ENABLE_FEATURE_FLAG_'.
        # For example:
        ### ("ENABLE_FEATURE_FLAG_SECRET_KEY", "{{ 24|random_string }}"),
    ]
)

hooks.Filters.CONFIG_OVERRIDES.add_items(
    [
        # Danger zone!
        # Add values to override settings from Tutor core or other plugins here.
        # Each override is a pair: (setting_name, new_value). For example:
        ### ("PLATFORM_NAME", "My platform"),
    ]
)


########################################
# INITIALIZATION TASKS
########################################

# To add a custom initialization task, create a bash script template under:
# tutorenable_feature_flag/templates/enable-feature-flag/jobs/init/
# and then add it to the MY_INIT_TASKS list. Each task is in the format:
# ("<service>", ("<path>", "<to>", "<script>", "<template>"))
MY_INIT_TASKS: list[tuple[str, tuple[str, ...]]] = [
    # For example, to add LMS initialization steps, you could add the script template at:
    # tutorenable_feature_flag/templates/enable-feature-flag/jobs/init/lms.sh
    # And then add the line:
    ### ("lms", ("enable-feature-flag", "jobs", "init", "lms.sh")),
]


# For each task added to MY_INIT_TASKS, we load the task template
# and add it to the CLI_DO_INIT_TASKS filter, which tells Tutor to
# run it as part of the `init` job.
for service, template_path in MY_INIT_TASKS:
    full_path: str = pkg_resources.resource_filename(
        "tutorenable_feature_flag", os.path.join("templates", *template_path)
    )
    with open(full_path, encoding="utf-8") as init_task_file:
        init_task: str = init_task_file.read()
    hooks.Filters.CLI_DO_INIT_TASKS.add_item((service, init_task))


########################################
# DOCKER IMAGE MANAGEMENT
########################################


# Images to be built by `tutor images build`.
# Each item is a quadruple in the form:
#     ("<tutor_image_name>", ("path", "to", "build", "dir"), "<docker_image_tag>", "<build_args>")
hooks.Filters.IMAGES_BUILD.add_items(
    [
        # To build `myimage` with `tutor images build myimage`,
        # you would add a Dockerfile to templates/enable-feature-flag/build/myimage,
        # and then write:
        ### (
        ###     "myimage",
        ###     ("plugins", "enable-feature-flag", "build", "myimage"),
        ###     "docker.io/myimage:{{ ENABLE_FEATURE_FLAG_VERSION }}",
        ###     (),
        ### ),
    ]
)


# Images to be pulled as part of `tutor images pull`.
# Each item is a pair in the form:
#     ("<tutor_image_name>", "<docker_image_tag>")
hooks.Filters.IMAGES_PULL.add_items(
    [
        # To pull `myimage` with `tutor images pull myimage`, you would write:
        ### (
        ###     "myimage",
        ###     "docker.io/myimage:{{ ENABLE_FEATURE_FLAG_VERSION }}",
        ### ),
    ]
)


# Images to be pushed as part of `tutor images push`.
# Each item is a pair in the form:
#     ("<tutor_image_name>", "<docker_image_tag>")
hooks.Filters.IMAGES_PUSH.add_items(
    [
        # To push `myimage` with `tutor images push myimage`, you would write:
        ### (
        ###     "myimage",
        ###     "docker.io/myimage:{{ ENABLE_FEATURE_FLAG_VERSION }}",
        ### ),
    ]
)


########################################
# TEMPLATE RENDERING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

hooks.Filters.ENV_TEMPLATE_ROOTS.add_items(
    # Root paths for template files, relative to the project root.
    [
        pkg_resources.resource_filename("tutorenable_feature_flag", "templates"),
    ]
)

hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    # For each pair (source_path, destination_path):
    # templates at ``source_path`` (relative to your ENV_TEMPLATE_ROOTS) will be
    # rendered to ``source_path/destination_path`` (relative to your Tutor environment).
    # For example, ``tutorenable_feature_flag/templates/enable-feature-flag/build``
    # will be rendered to ``$(tutor config printroot)/env/plugins/enable-feature-flag/build``.
    [
        ("enable-feature-flag/build", "plugins"),
        ("enable-feature-flag/apps", "plugins"),
    ],
)


########################################
# PATCH LOADING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

# For each file in tutorenable_feature_flag/patches,
# apply a patch based on the file's name and contents.
for path in glob(
    os.path.join(
        pkg_resources.resource_filename("tutorenable_feature_flag", "patches"),
        "*",
    )
):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))


########################################
# CUSTOM JOBS (a.k.a. "do-commands")
########################################

# A job is a set of tasks, each of which run inside a certain container.
# Jobs are invoked using the `do` command, for example: `tutor local do importdemocourse`.
# A few jobs are built in to Tutor, such as `init` and `createuser`.
# You can also add your own custom jobs:

# To add a custom job, define a Click command that returns a list of tasks,
# where each task is a pair in the form ("<service>", "<shell_command>").
# For example:
### @click.command()
### @click.option("-n", "--name", default="plugin developer")
### def say_hi(name: str) -> list[tuple[str, str]]:
###     """
###     An example job that just prints 'hello' from within both LMS and CMS.
###     """
###     return [
###         ("lms", f"echo 'Hello from LMS, {name}!'"),
###         ("cms", f"echo 'Hello from CMS, {name}!'"),
###     ]


# Then, add the command function to CLI_DO_COMMANDS:
## hooks.Filters.CLI_DO_COMMANDS.add_item(say_hi)

# Now, you can run your job like this:
#   $ tutor local do say-hi --name="Jillian Vogel"


#######################################
# CUSTOM CLI COMMANDS
#######################################

# Your plugin can also add custom commands directly to the Tutor CLI.
# These commands are run directly on the user's host computer
# (unlike jobs, which are run in containers).

# To define a command group for your plugin, you would define a Click
# group and then add it to CLI_COMMANDS:


### @click.group()
### def enable-feature-flag() -> None:
###     pass


### hooks.Filters.CLI_COMMANDS.add_item(enable-feature-flag)


# Then, you would add subcommands directly to the Click group, for example:


### @enable-feature-flag.command()
### def example_command() -> None:
###     """
###     This is helptext for an example command.
###     """
###     print("You've run an example command.")


# This would allow you to run:
#   $ tutor enable-feature-flag example-command
from tutormfe.hooks import PLUGIN_SLOTS
PLUGIN_SLOTS.add_items([
  (
    "all",
    "learning_logged_out_items_slot",
    """
    {
      op: PLUGIN_OPERATIONS.Modify,
      widgetId: 'default_contents',
      fn: (widget) => {
        widget.content.buttonsInfo = [
          {
            href: 'https://docs.openedx.org/en/latest/',
            message: 'Documentation'
          },
          {
            href: 'https://discuss.openedx.org/',
            message: 'Forums'
          },
          {
            href: 'https://openedx.org/',
            message: 'openedx.org',
            variant: 'primary'
          }
        ];
        return widget;
      }
    }
    """
  )
])

PLUGIN_SLOTS.add_items([
    # Hide the default footer
    (
        "all",
        "footer_slot",
        """
        {
          op: PLUGIN_OPERATIONS.Hide,
          widgetId: 'default_contents',
        }"""
    ),
    # Insert a custom footer
    (
        "all",
        "footer_slot",
        """
        {
          op: PLUGIN_OPERATIONS.Insert,
          widget: {
            id: 'custom_footer',
            type: DIRECT_PLUGIN,
            RenderWidget: () => (
               <>
                {/* --- Estilos específicos para el footer --- */}
                <style>{`
                  .custom-footer a {
                    color: #000;
                    text-decoration: none;
                    transition: color 0.2s ease;
                  }
                  .custom-footer a:hover {
                    color: #0275d8;
                  }
                `}</style>

                {/* --- Estructura del footer --- */}
                <footer className="custom-footer" style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  borderTop: '1px solid #ccc',
                  padding: '1.5rem 2rem',
                  backgroundColor: '#fff',
                  fontSize: '0.9rem',
                }}>
                  {/* Enlaces centrados */}
                  <nav style={{
                    display: 'flex',
                    gap: '1.5rem',
                    marginBottom: '0.5rem',
                  }}>
                    <a href="https://apps.app.academusdigital.com/learning/course/course-v1:Unimec+CBIBAD001+2025_ABR">Biblioteca</a>
                    <a href="https://www.academusdigital.com/faq/">Preguntas Frecuentes</a>
                    <a href="https://www.academusdigital.com/contact/">Contáctanos</a>
                  </nav>
                  {/* Copyright centrado */}
                  <div>Copyrights ©2025. Academus Digital.</div>
                </footer>
              </>
            ),
          },
        }"""
    )
])
PLUGIN_SLOTS.add_items([
  (
    "all",
    "logo_slot",
    """
    {
      op: PLUGIN_OPERATIONS.Hide,
      widgetId: 'default_contents',
    }"""
  ),
  (
    "all",
    "logo_slot",
    """
    {
      op: PLUGIN_OPERATIONS.Insert,
      widget: {
        id: 'custom_logo_component',
        type: DIRECT_PLUGIN,
        RenderWidget: () => (
          <img
            src="https://raw.githubusercontent.com/Edwin75206/tutor-contrib-enable-feature-flag/refs/heads/main/images/logo.png"
            alt="Academus Digital"
            style={{
              height: '40px',
              width: 'auto',
              marginRight: '1rem',   
              alignSelf: 'center'   
            }}
          />
        ),
      },
    }"""
  )
])


PLUGIN_SLOTS.add_items([
    (
        "all",
        "learning_user_menu_slot",
        """
        {
          op: PLUGIN_OPERATIONS.Insert,
          widget: {
            id: 'custom_library_link',
            type: DIRECT_PLUGIN,
            priority: 20,
            RenderWidget: () => (
               <a
                className="dropdown-item"
                href="https://apps.app.academusdigital.com/learning/course/course-v1:Unimec+CBIBAD001+2025_ABR"
                target="_blank"
                rel="noopener noreferrer"
              >
                Biblioteca
              </a>
            ),
          },
        }
        """
    )
])

hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-lms-common-settings",
        """
MFE_CONFIG["FAVICON_URL"] = "https://raw.githubusercontent.com/Edwin75206/tutor-contrib-enable-feature-flag/refs/heads/main/images/favicon.ico"
"""
    )
)