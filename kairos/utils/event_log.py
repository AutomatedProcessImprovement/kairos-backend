from pandas import read_csv

import pm4py

def get_dataframe_from_file(file, delimiter):
    extension = file.filename.rsplit('.', 1)[1].lower()
    if extension == "xes":
        df = get_dataframe_from_xes(file)
    elif extension == "csv":
        df = get_dataframe_from_csv(file, delimiter)
    else:
        df = None
    return df

def get_dataframe_from_xes(file):
    df = pm4py.read_xes(file)
    df = pm4py.convert_to_dataframe(df)
    return df

def get_dataframe_from_csv(file, delimiter):
    df = read_csv(file, sep=delimiter)
    return df

# def get_dataframe_from_compressed_file(file, delimiter):
#     try:
#         file_type = detect_file_type(file)
#         if file_type == "zip":
#             with ZipFile(file) as zip_file:
#                 result = get_result_dataframe_from_compressed_file(zip_file, delimiter)
#         elif file_type == "gzip":
#             with GzipFile(file) as gzip_file:
#                 result = get_result_dataframe_from_compressed_file(gzip_file, delimiter)
#         else:
#             raise Exception('Bad zip file.')
#     except Exception as e:
#         raise e
#     return result


# def get_result_dataframe_from_compressed_file(file, delimiter):
#     result = None
#     temp_path = ""

#     try:
#         if isinstance(file, ZipFile):
#             name_list = file.namelist()
#         elif isinstance(file, GzipFile):
#             if file.read(10).startswith(b"<?xml"):
#                 name_list = ["file.xes"]
#             else:
#                 name_list = ["file.csv"]
#             file.seek(0)
#         else:
#             raise ValueError(ErrorType.EVENT_LOG_BAD_ZIP)

#         filtered_name_list = [name for name in name_list if name not in path.EXCLUDED_EXTRACTED_FILE_NAMES]

#         if len(filtered_name_list) != 1:
#             raise HTTPException(status_code=400, detail="Zip file should contain only one file")

#         filename = filtered_name_list[0]
#         extension = get_extension(filename)

#         if extension not in path.ALLOWED_EXTRACTED_EXTENSIONS:
#             raise HTTPException(status_code=400, detail="Zip file should contain only xes or csv file")

#         temp_path = get_new_path(base_path=f"{path.TEMP_PATH}/", suffix=f".{extension}")

#         with open(temp_path, "wb") as f:
#             f.write(file.read(filename) if isinstance(file, ZipFile) else file.read())

#         if extension == "xes":
#             result = get_dataframe_from_xes(temp_path)
#         elif extension == "csv":
#             result = get_dataframe_from_csv(temp_path, delimiter)
#     finally:
#         delete_file(temp_path)

#     return result


# def detect_file_type(file_path):
#     with open(file_path, "rb") as file:
#         file_signature = file.read(2)
#     if file_signature == b"\x50\x4b":  # PK (ZIP file signature)
#         return "zip"
#     elif file_signature == b"\x1f\x8b":  # 1F 8B (gzip file signature)
#         return "gzip"
#     return "unknown"