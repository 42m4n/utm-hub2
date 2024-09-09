import pyodbc
from django.core.cache import cache

from common.conf import Database
from common.logger import logger


def get_lansweeper_data(asset_name, row_count):
    cursor = None
    connection = None
    try:
        # Check if the data is already cached
        cache_key = f"lansweeper_data:{asset_name}:{row_count}"
        cached_data = None
        try:
            cached_data = cache.get(cache_key)
        except Exception as e:
            logger.warning(f"could not access cache: {e}")
        if cached_data:
            return cached_data
        query = f"""
            SELECT TOP {row_count} tblassets.AssetID,
            tblassets.AssetName,
            tblassets.IPAddress
            FROM tblassets
            INNER JOIN tblassetcustom ON tblassets.AssetID = tblassetcustom.AssetID
            INNER JOIN tsysassettypes ON tsysassettypes.AssetType = tblassets.Assettype
            WHERE tblassetcustom.State = 1 AND tsysassettypes.AssetTypename IN ('Linux', 'Windows')
            """

        if asset_name:
            query += " AND tblassets.AssetName LIKE " + "'" + asset_name + "%'"

        query += " ORDER BY tblassets.AssetID"

        connection_string = f"""
            DRIVER={Database.odbc_driver()[0]};
            SERVER={Database.host};
            DATABASE={Database.db_name};
            UID={Database.user};
            PWD={Database.password};
            TrustServerCertificate=yes;"""
        logger.info("Connecting to lansweeper db")

        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        cursor.execute(query)
        logger.info("Execute query on lansweeper db")

        data = cursor.fetchall()

        json_data = [
            {
                'id': row[0],
                'name': f'{row[1]} [{row[2]}]',
                'ip': row[2]
            }
            for row in data
        ]
        try:
            cache.set(cache_key, json_data)
        except Exception as e:
            logger.warning(f"Could not set cache: {e}")

        return json_data

    except Exception as e:
        logger.error(f"Getting lansweeper data encountered an error: {e}")

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
            logger.info("Close Lansweeper DB connection")
