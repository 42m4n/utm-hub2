import json

from apps.paasapp.serilizers import PaasSerializer
from common.logger import logger
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..modules.terraform import create_requests_obj
from ..tasks import create_tf_files_v2


class ApiPaasViewV2(APIView):

    def post(self, request):
        """_summary_

        Args:
            request (json): data form serializer

        Returns:
            response: status
        """
        serializer = PaasSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                if serializer.is_valid():
                    serializer_validated_data = json.loads(
                        serializer.validated_data["content"]
                    )
                    resources = serializer_validated_data["request"]["udf_fields"]
                    ticket_number = serializer_validated_data["request"]["id"]
                    try:
                        request_obj = create_requests_obj(resources)
                        utm_name = request_obj.get("utm_name")
                        create_tf_files_v2(resources, ticket_number, utm_name)
                    except Exception as error:
                        logger.error(f"Error in create_tf_files: {error}")
                        return Response(
                            {"response": [{"status": "not ok"}]},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )
                    return Response(
                        {"response": [{"status": "ok"}]}, status=status.HTTP_200_OK
                    )
            except Exception as error:
                logger.error(f" Error at ApiPaasView : {error} ")
            return Response(
                {"response": [{"status": "not ok"}]}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
