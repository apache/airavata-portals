from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from django_airavata.apps.api import launcher_client, launcher_serializers


def _client(request: Request) -> launcher_client.LauncherClient:
    token = request.session.get("ACCESS_TOKEN", "")
    return launcher_client.get_client(user_token=token, request=request)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def applications_list(request: Request) -> Response:
    category = request.query_params.get("category") or None
    search = request.query_params.get("search") or None
    results = _client(request).list_applications(category=category, search=search)
    return Response({"results": results})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def application_detail(request: Request, app_id: str) -> Response:
    try:
        return Response(_client(request).get_application(app_id=app_id))
    except LookupError:
        raise NotFound()


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def project_resource_profile(request: Request, project_id: str) -> Response:
    return Response(_client(request).get_project_resource_profile(project_id=project_id))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def user_storages(request: Request) -> Response:
    return Response({"results": _client(request).list_user_storages()})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def projects_list(request: Request) -> Response:
    return Response({"results": _client(request).list_projects()})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def experiment_draft_preview(request: Request) -> Response:
    serializer = launcher_serializers.ExperimentDraftSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        result = _client(request).generate_preview(serializer.validated_data)
    except ConnectionError as e:
        return Response({"message": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
    return Response(result)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def experiment_draft_create(request: Request) -> Response:
    serializer = launcher_serializers.ExperimentDraftSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        result = _client(request).launch_experiment(serializer.validated_data)
    except ConnectionError as e:
        return Response({"message": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
    return Response(result, status=status.HTTP_201_CREATED)
