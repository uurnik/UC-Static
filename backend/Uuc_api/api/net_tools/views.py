import subprocess
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse


@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def ping(request):
    response = subprocess.Popen(
        ["ping", "-c", "4", request.data["query"]], stdout=subprocess.PIPE
    )
    response.wait()
    output = response.stdout.read().decode()

    return JsonResponse({"output": output})


@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def nslookup(request):
    response = subprocess.Popen(
        ["nslookup", request.data["query"]], stdout=subprocess.PIPE
    )
    response.wait()
    output = response.stdout.read().decode()

    return JsonResponse({"output": output})


@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def traceroute(request):
    response = subprocess.Popen(
        ["traceroute", request.data["query"]], stdout=subprocess.PIPE
    )
    response.wait()
    output = response.stdout.read().decode()

    return JsonResponse({"output": output})
