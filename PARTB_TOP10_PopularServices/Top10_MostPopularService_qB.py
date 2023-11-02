"""Question - 2 (PartB)
"""
import sys, string
import os
import socket
import time
import operator
import boto3
import json
from pyspark.sql import SparkSession
from datetime import datetime
import pandas as pd
import json

if __name__ == "__main__":

    spark = SparkSession\
        .builder\
        .appName("Q2_")\
        .getOrCreate()

    def good_line(line):
        try:
            fields = line.split(',')
            if len(fields)!=15:
                return False
            int(fields[11])
            return True
        except:
            return False
        
    def good_line_con(line):
        try:
            fields = line.split(',')
            if len(fields)!=6:
                return False
            return True
        except:
            return False

    # shared read-only object bucket containing datasets
    s3_data_repository_bucket = os.environ['DATA_REPOSITORY_BUCKET']

    s3_endpoint_url = os.environ['S3_ENDPOINT_URL']+':'+os.environ['BUCKET_PORT']
    s3_access_key_id = os.environ['AWS_ACCESS_KEY_ID']
    s3_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
    s3_bucket = os.environ['BUCKET_NAME']

    hadoopConf = spark.sparkContext._jsc.hadoopConfiguration()
    hadoopConf.set("fs.s3a.endpoint", s3_endpoint_url)
    hadoopConf.set("fs.s3a.access.key", s3_access_key_id)
    hadoopConf.set("fs.s3a.secret.key", s3_secret_access_key)
    hadoopConf.set("fs.s3a.path.style.access", "true")
    hadoopConf.set("fs.s3a.connection.ssl.enabled", "false")

    lines_tr = spark.sparkContext.textFile("s3a://" + s3_data_repository_bucket + "/ECS765/ethereum-parvulus/transactions.csv")
    lines_con = spark.sparkContext.textFile("s3a://" + s3_data_repository_bucket + "/ECS765/ethereum-parvulus/contracts.csv")
    
    tr_clean_lines = lines_tr.filter(good_line)
    con_clean_lines = lines_con.filter(good_line_con)

    
    trans = tr_clean_lines.map(lambda x: (x.split(',')[6], int(x.split(',')[7])))
    cont = con_clean_lines.map(lambda x: (x.split(',')[0],1))
    transaction = trans.reduceByKey(lambda x, y: x + y)
    
    join_df = transaction.join(cont)                                      #join transaction adress field to contract tables to_adress field
    
    address_value=join_df.map(lambda x: (x[0], x[1][0]))
    top10 = address_value.takeOrdered(10, key=lambda x: -1*x[1])


    now = datetime.now() # current date and time
    date_time = now.strftime("%d-%m-%Y_%H:%M:%S")

    my_bucket_resource = boto3.resource('s3',
                endpoint_url='http://' + s3_endpoint_url,
                aws_access_key_id=s3_access_key_id,
                aws_secret_access_key=s3_secret_access_key)

    my_result_object = my_bucket_resource.Object(s3_bucket,'Q2_' + date_time + '/partB.txt')
    my_result_object.put(Body=json.dumps(top10))


    spark.stop()