from common.logger import logger
from apps.lansweeper.utilities import get_lansweeper_data
from django.http import JsonResponse
from rest_framework.views import APIView


class LansweeprView(APIView):

    def get(self, request):
        try:
            asset_name = None
            row_count = 10
            params = request.GET.get('input_data')
            if params:
                params = eval(params)
                asset_name = params.get('list_info').get('search_fields').get('name')
                row_count = int(params.get('list_info').get('row_count'))

            lansweeper_data = get_lansweeper_data(asset_name, row_count)
            return JsonResponse(
                {
                    "response_status": [
                        {
                            "status_code": 2000,
                            "status": "success"
                        }
                    ],
                    "list_info": {
                        "has_more_rows": True,
                        "start_index": 1,
                        "row_count": row_count
                    },
                    "assets": lansweeper_data
                })

        except Exception as error:
            logger.error(f'LansweeprView get error : {error} ')

            return JsonResponse(
                {"response_status":
                    {
                        "status_code": 4000,
                        "messages": [{"status_code": 4000, "type": "failed", "message": error}],
                        "status": "failed",
                    }
                }
            )
