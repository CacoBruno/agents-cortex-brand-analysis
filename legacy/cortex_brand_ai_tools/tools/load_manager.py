import requests
import time
from typing import Dict, Union, List
from io import StringIO
import pandas as pd
#from src.config import logger
from datetime import datetime
from decimal import Decimal
from datetime import datetime, timezone

import logging
import logging.handlers

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LOADMANAGER = "https://api.cortex-intelligence.com"
DATA_PARSER = {
    "charset": "UTF-8",
    "quote": '"',
    "escape": "\\",
    "delimiter": "\t",
    "fileType": "CSV",
    "encode": "UTF-8",
}
MAX_RETRIES = 2
BACKOFF_FACTOR = 0.2
BATCH_SIZE = 15000
DEFAULT_REGION = 'us-east-1'

class CortexUploadAPI:     
    
    def __init__(self, loadmanager_url: str = LOADMANAGER, data_parser: Dict[str, str] = DATA_PARSER, max_retries: int = 1, backoff_factor: float = 0.2, batch_size = BATCH_SIZE,
                 default_region = DEFAULT_REGION):
        self.loadmanager = loadmanager_url
        self.data_parser = data_parser
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.batch_size = batch_size
        self.default_region = default_region

    
    def rearrange_df_to_sid(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Reorder the DataFrame rows to move non-null values to the top,
        helping with type detection in SID. 
        """
        df = df.reset_index(drop=True)
        target_rows = set()
        for col in df.columns:
            target_row = df.loc[:, col].first_valid_index()
            if target_row is not None and target_row >= 500:
                target_rows.add(target_row)
        idx = list(target_rows) + [i for i in range(len(df)) if i not in target_rows]
        return df.iloc[idx].reset_index(drop=True)
    
    def make_file_obj_from_dataframe(self, df: pd.DataFrame, index=False, sep="\t", encoding="UTF-8", quotechar='"') -> StringIO:
        """
        Create a file-like object from a DataFrame.
        """
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=index, sep=sep, encoding=encoding, quotechar=quotechar)
        csv_buffer.seek(0) 
        return csv_buffer


    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        retries = 0
        while retries <= self.max_retries:
            try:
                response = requests.request(method, self.loadmanager + endpoint, **kwargs)
                return response
            except requests.exceptions.RequestException as e:
                retries += 1
                sleep_time = self.backoff_factor * (2 ** (retries - 1)) 
                logger.warning(f"Request failed: {str(e)}. Retrying in {sleep_time}s ({retries}/{self.max_retries})...")
                time.sleep(sleep_time)
                if retries > self.max_retries:
                    raise    

    
    def get_bearer_token(self, client: str, credentials: Dict[str, str]) -> Dict[str, str]:
        url = f"https://{client}.cortex-intelligence.com/service/integration-authorization-service.login"
        response = requests.request("POST", url, json=credentials)
        return {"Authorization": "Bearer " + response.json()["key"]}

    def upload_to_ctx(self, df: pd.DataFrame, cube_id: str, client: str, credentials: Dict[str, str], filename: str) -> Dict[str, Union[str, int, bool]]:
        
        num_records = len(df)
        num_batches = -(-len(df) // self.batch_size)
        
        logger.info(f"{num_records} records detected, dividing into {num_batches} batches for upload.")
        headers = self.get_bearer_token(client, credentials)
        
        responses = {}
        for i in range(num_batches):
            
            start_time = time.time()
            
            batch_df = df.iloc[i * self.batch_size: (i + 1) * self.batch_size]  # Seleciona o lote de dados
            batch_df = self.rearrange_df_to_sid(batch_df)  # Reorganiza o lote
            file_obj = self.make_file_obj_from_dataframe(batch_df)
            logger.info(f"Uploading batch {i + 1} of {num_batches}.")           
            
            
            content = {
                "destinationId": cube_id,
                "fileProcessingTimeout": 3600,
                "executionTimeout": 3600
            }

            data_input_id = self._request("POST", "/datainput", headers=headers, json=content).json()["id"]

            execution_id = self._request(
                "POST",
                f"/datainput/{data_input_id}/execution",
                headers=headers,
                json=content,
            ).json()["executionId"]
            
            file_obj = self.make_file_obj_from_dataframe(batch_df)

            self._request(
                "POST",
                f"/execution/{execution_id}/file",
                headers=headers,
                data=self.data_parser,
                files={"file": file_obj},
            )

            self._request("PUT", f"/execution/{execution_id}/start", headers=headers)
            
            responses[f"batch_{i + 1}"] = {"data_input_id": data_input_id, "execution_id": execution_id}
            
            
        #    elapsed_time_ms = (time.time() - start_time) * 1000
         #   total_memory_usage_bytes = int(batch_df.memory_usage(deep=True).sum())
            
#            self.save_to_dynamodb(
 #               client_name=client,
  #              cube_id=cube_id,
#                num_records=len(batch_df),
 #               execution_id=execution_id, 
  #              filename=filename,  
  #              elapsed_time_ms=elapsed_time_ms,
   #             total_memory_usage_bytes=total_memory_usage_bytes  
    #        )
  #          logger.info(f"Batch {i + 1}/{num_batches} uploaded successfully in {elapsed_time_ms:.2f}ms and info saved to DynamoDB.")
   #         logger.info(f"Execution ID: {execution_id}")
        
        return responses
    
    