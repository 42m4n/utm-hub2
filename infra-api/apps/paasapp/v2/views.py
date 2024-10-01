import json
import requests

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.paasapp.serilizers import PaasSerializer
from common.conf import UTM
from common.conf import Redis as RedisConf
from common.logger import logger
from common.conf import ManageEngine as ME

from ..modules.terraform import create_requests_obj
from ..modules.utm import UTMHandler
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
                        if not any(utm["UTM_NAME"] == utm_name for utm in UTM.utms):
                            logger.info(f"utm {utm_name} is not in the configurations.")
                            return Response(
                                {"error": "UTM name is not valid."},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        create_tf_files_v2(resources, ticket_number, utm_name)
                    except Exception as error:
                        logger.error(f"Error in create_tf_files: {error}")
                        # Sending error status code into ManageEngine
                        ticket_url = (
                            f"{ME.manage_engine_address}/api/v3/requests/{ticket_number}"
                        )
                        response = requests.put(
                            url=ticket_url,
                            headers={"authtoken": f"{ME.manage_engine_token}"},
                            data={"input_data": str({"request": {"status": {"id": ME.manage_engine_error_status}}})},
                            verify=False
                        )
                        response.raise_for_status()
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


class UTMPoliciesView(APIView):
    def get(self, request):
        utm_name = request.GET.get("utm_name")
        if not utm_name:
            return Response(
                {"error": "UTM name is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not any(utm["UTM_NAME"] == utm_name for utm in UTM.utms):
            return Response(
                {"error": "UTM name is not valid."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            utm_handler = UTMHandler(utm_name)
            policies = utm_handler.get_policies_from_utm()

            # Store policies in Redis
            redis_key = f"{utm_name}_policies"
            RedisConf.redis_client.set(redis_key, json.dumps(policies))
            logger.info("Policies fetched and stored in Redis successfully")

            return Response(
                {"message": "Policies fetched and stored in Redis successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
