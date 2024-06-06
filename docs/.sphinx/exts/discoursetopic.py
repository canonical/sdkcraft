import re
import requests
from sphinx.errors import ExtensionError


def get_topic_id(url, slug):
    endpoint = f"{url}/t/{slug}.json"
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            return response.json().get("id")
        else:
            return None
    except requests.RequestException as e:
        raise ExtensionError(f"Error retrieving topic ID: {e}")


def slugify(pagename):
    slug = re.sub(r"[^a-z0-9\s-]", "", pagename.lower())
    slug = slug.replace(" ", "-")
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")

    return slug


def setup_func(app, pagename, templatename, context, doctree):

    def discourse_topic(slug):
        topic_id = get_topic_id(context["discourse"], slug)

        if topic_id:
            url = f"{context['discourse']}t/{topic_id}"
        else:
            url = f"{context['discourse']}new-topic?title={slug}&tags=docs"
            if "category" in context:
                url += f"&category={context['category']}"

        return url

    context["discourse_topic"] = discourse_topic


def setup(app):
    app.connect("html-page-context", setup_func)
