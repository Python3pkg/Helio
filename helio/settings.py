import os

COMPONENT_BASE_DIRECTORIES = (os.path.join(os.getcwd(), 'components'),)
VIEWSTATE_MANAGER_SESSION_KEY = 'helio_viewstates'
TEMPLATE_RENDERER = 'helio.django.renderers.render'