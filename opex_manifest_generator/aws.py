import boto3

def opex_to_s3(bucket, root, access_key = None, secret_key = None, session_token = None):
    session = boto3.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                                            aws_session_token=session_token)
    s3 = session.client(service_name="s3")

    def list_recurse(bucket, delimiter, prefix, number = 1):
        
        r = s3.list_objects_v2(Bucket=bucket,Delimiter=delimiter,Prefix=prefix)
        try:
            for obj in r['Contents'][1:]:
                name = obj.get('Key')
                size = obj.get('Size')
                md5 = obj.get('ETag')
                level = len(list(filter(None,name.split("/"))))
                print(name, number, level)
                number += 1
        except: 
            number = 1
        try:
            for obj in r['CommonPrefixes']:
                name = obj.get('Prefix')
                level = len(list(filter(None,name.split("/"))))               
                print(name, number, level)
                number += 1
                list_recurse(bucket=bucket,delimiter=delimiter,prefix=obj['Prefix'], number = 1)
        except:
            number = 1

    list_recurse(bucket=bucket,delimiter="/",prefix=root, number = 1)