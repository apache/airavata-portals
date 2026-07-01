from django_airavata.apps.api.queue_settings import queue_settings_calculator

# See https://apache-airavata-django-portal.readthedocs.io/en/latest/dev/queue_settings_calculator/ for more information
@queue_settings_calculator(
    id="{{ cookiecutter.project_slug}}-my-queue-settings-calculator", name="{{ cookiecutter.project_name}}: My Queue Settings Calculator"
)
def my_queue_settings_calculator(request, experiment_model):
    # experiment_model is a proto ExperimentModel
    # (airavata_sdk.generated...model.experiment.experiment_pb2.ExperimentModel)

    # TODO: Implement logic here to determine appropriate queue settings for experiment_model
    total_core_count = 4
    queue_name = "shared"
    node_count = 1
    walltime_limit = 30

    # Return a dictionary with the queue settings values
    result = {}
    result["totalCPUCount"] = total_core_count
    result["queueName"] = queue_name
    result["nodeCount"] = node_count
    result["wallTimeLimit"] = walltime_limit
    return result
