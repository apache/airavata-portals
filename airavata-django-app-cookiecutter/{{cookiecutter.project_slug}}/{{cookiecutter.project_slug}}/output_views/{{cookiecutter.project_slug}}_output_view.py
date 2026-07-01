from django.conf import settings
{% if cookiecutter.output_view_display_type == "image" %}
import io
{% elif cookiecutter.output_view_display_type == "html" %}
from django.template.loader import render_to_string
{% endif %}


class {{ cookiecutter.output_view_provider_class_name }}:
    display_type = "{{ cookiecutter.output_view_display_type }}"
    # As a performance optimization, the output view provider can be invoked
    # immediately instead of only after being selected by the user in the
    # portal.  Set to True to invoke immediately. Only use this with simple
    # output view providers that return quickly
    immediate = False
    name = "{{ cookiecutter.project_name }}"

    def generate_data(self, request, experiment_output, experiment,{% if "single" in cookiecutter.number_of_output_files %} output_file=None,{% else %} output_files=None,{% endif %} **kwargs):

        # Use `output_file` or `output_files` to read from the output file(s).
        # See https://docs.python.org/3/tutorial/inputoutput.html#methods-of-file-objects
        # for how to read from file objects. For example, to read the entire file, use:
        #
        # entire_file = output_file.read()


        # Example code: user storage
        # To find other files in the experiment data directory, use the storage
        # facade to list the experiment's data directory:
        #
        # listing = request.airavata.storage.list_experiment_dir(experiment.experiment_id)
        #
        # Each entry carries a path you can read the bytes of:
        #
        # data = request.airavata.storage.download_file(listing.files[0].path).content


        # Example code: Airavata API client
        # Make calls to the Airavata API via the gRPC facades, for example load
        # the DataProduct for this output file:
        #
        # data_product = request.airavata.research.get_data_product(experiment_output.value)
        #
        # 'experiment_output.value' is the Data Product URI for the output file.
        # The returned DataProductModel carries metadata about the output file and
        # the location(s) where it is stored. The gRPC client is 'request.airavata'
        # with one facade per service (research / compute / storage / ...);
        # authentication is carried automatically and 'settings.GATEWAY_ID' is the
        # gateway id.


    {% if cookiecutter.output_view_display_type == "link" %}
        label = "Link to Google"
        url = "https://google.com"
        return {
            "label": label,
            "url": url
        }
    {% elif cookiecutter.output_view_display_type == "image" %}
        # Typical thing is to write an image to an in-memory BytesIO object and
        # then return its bytes
        buffer = io.BytesIO()
        # Example: say you have a figure object, which is an instance of
        # matplotlib's Figure. Then you can write it to the BytesIO object
        # figure.savefig(buffer, format='png')
        image_bytes = buffer.getvalue()
        buffer.close()
        return {
            'image': image_bytes,
            'mime-type': 'image/png'
        }
    {% elif cookiecutter.output_view_display_type == "html" %}
        # Return a dictionary with 'output' as the HTML string and 'js' as the
        # absolute URL to a JavaScript file to load for the view
        # In the example code, the HTML is produced from a Django template, but
        # you don't have to do it that way.
        html_context = {}  # extra context
        html_string = render_to_string('path/to/template.html', html_context)
        js_abs_path = "/static/path/to/script.js"
        return {
            'output': html_string,
            'js': js_abs_path
        }
    {% endif %}
